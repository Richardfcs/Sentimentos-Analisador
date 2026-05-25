"""
ai_service.py — Módulo de comunicação com a IA via OpenRouter com Cache e Paralelismo

Encapsula toda a lógica de processamento dos comentários:
1. Filtra comentários que já possuem análise no cache local (SQLite)
2. Envia os comentários novos em lotes (batches) em paralelo (ThreadPoolExecutor)
3. Armazena os novos resultados de volta no cache local
4. Retorna a lista unificada de análises e metadados de performance.
"""

import os
import json
import re
import time
import logging
import requests
import concurrent.futures
from schemas import AnaliseIA
import cache_service

logger = logging.getLogger(__name__)

# Modelo gratuito recomendado do OpenRouter
MODELO_PADRAO = "openrouter/free"

PROMPT_SISTEMA = """Você é um analisador de sentimentos especializado em avaliações de clientes brasileiros.

Para cada comentário que receber, você deve retornar um objeto JSON com EXATAMENTE estes campos:
- "sentimento": deve ser "positivo", "negativo" ou "neutro"
- "emocao": uma palavra sem acentos (satisfacao, frustracao, raiva, confianca, duvida, surpresa, gratidao, decepcao)
- "confianca": número decimal de 0.0 a 1.0 indicando sua confiança na classificação
- "nivel_criticidade": deve ser "baixo", "medio" ou "alto"
- "pontos_positivos": lista de strings curtas com aspectos elogiados (lista vazia se não houver)
- "pontos_negativos": lista de strings curtas com problemas citados (lista vazia se não houver)
- "resumo": uma frase curta resumindo o sentimento do comentário

REGRAS IMPORTANTES:
1. Retorne APENAS um array JSON válido, sem texto adicional, sem markdown, sem explicações.
2. A ordem dos objetos no array deve corresponder à ordem dos comentários recebidos.
3. Cada objeto deve ter TODOS os 7 campos listados acima.
4. O campo "emocao" deve ser UMA ÚNICA PALAVRA sem acentos."""


def _extrair_json_da_resposta(texto: str) -> list[dict]:
    """Tenta extrair um array JSON válido da resposta da IA usando diferentes estratégias."""
    # Estratégia 1: parse direto
    try:
        resultado = json.loads(texto)
        if isinstance(resultado, list):
            return resultado
        if isinstance(resultado, dict):
            return [resultado]
    except json.JSONDecodeError:
        pass

    # Estratégia 2: extrair array JSON com regex
    match = re.search(r'\[[\s\S]*\]', texto)
    if match:
        try:
            resultado = json.loads(match.group())
            if isinstance(resultado, list):
                return resultado
        except json.JSONDecodeError:
            pass

    # Estratégia 3: extrair blocos de código markdown
    match = re.search(r'```(?:json)?\s*([\s\S]*?)```', texto)
    if match:
        try:
            resultado = json.loads(match.group(1))
            if isinstance(resultado, list):
                return resultado
            if isinstance(resultado, dict):
                return [resultado]
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Não foi possível extrair JSON válido da resposta da IA: {texto[:200]}...")


def _processar_lote_ia(lote: list[dict], api_key: str, num_lote: int, total_lotes: int) -> list[AnaliseIA]:
    """Realiza a chamada HTTP e validação Pydantic para um único lote de comentários, com retentativas."""
    # Monta a lista de comentários para o prompt
    comentarios_formatados = "\n".join(
        f'{i+1}. (ID {c["id"]}): "{c["comentario"]}"'
        for i, c in enumerate(lote)
    )

    prompt_usuario = f"""Analise os {len(lote)} comentários abaixo e retorne um array JSON com a análise de cada um, na mesma ordem:

{comentarios_formatados}"""

    max_tentativas = 3
    for tentativa in range(1, max_tentativas + 1):
        logger.info(f"Lote {num_lote}/{total_lotes}: tentativa {tentativa}/{max_tentativas} ({len(lote)} comentários)...")
        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:5000",
                    "X-Title": "Analisador de Sentimentos",
                },
                json={
                    "model": MODELO_PADRAO,
                    "messages": [
                        {"role": "system", "content": PROMPT_SISTEMA},
                        {"role": "user", "content": prompt_usuario},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 3000,
                },
                timeout=60,
            )

            if response.status_code == 402:
                raise ValueError(
                    "Erro de pagamento (402 Payment Required) no OpenRouter. "
                    "Adicione créditos na sua conta ou aguarde o reset diário para contas gratuitas."
                )
            elif response.status_code == 401:
                raise ValueError(
                    "Erro de autenticação (401 Unauthorized) no OpenRouter. Verifique sua chave no arquivo .env."
                )
            elif response.status_code == 429:
                logger.warning(f"Lote {num_lote}: Recebeu 429 (Too Many Requests). Aguardando para tentar novamente...")
                time.sleep(3 * tentativa)
                continue

            response.raise_for_status()
            dados_resposta = response.json()
            texto_resposta = dados_resposta["choices"][0]["message"]["content"]
            logger.info(f"Resposta recebida para o lote {num_lote} na tentativa {tentativa} ({len(texto_resposta)} caracteres)")

            # Parseia o JSON
            analises_raw = _extrair_json_da_resposta(texto_resposta)
            
            # Se a resposta foi truncada e não retornou todas as análises, força uma exceção para tentar novamente
            if len(analises_raw) < len(lote):
                raise ValueError(f"Resposta incompleta/truncada (recebeu {len(analises_raw)} de {len(lote)} análises)")

            # Valida cada resposta
            lote_analises_validadas = []
            for i, analise_dict in enumerate(analises_raw):
                analise = AnaliseIA.model_validate(analise_dict)
                lote_analises_validadas.append(analise)

            return lote_analises_validadas[:len(lote)]

        except Exception as e:
            logger.warning(f"Erro no lote {num_lote} (tentativa {tentativa}/{max_tentativas}): {e}")
            if tentativa < max_tentativas:
                time.sleep(2 * tentativa)
            else:
                logger.error(f"Lote {num_lote}: Falha definitiva após {max_tentativas} tentativas. Aplicando fallbacks.")
                # Preencher com fallbacks caso as tentativas tenham falhado
                lote_analises_validadas = []
                while len(lote_analises_validadas) < len(lote):
                    lote_analises_validadas.append(AnaliseIA(
                        sentimento="neutro",
                        emocao="indefinido",
                        confianca=0.0,
                        nivel_criticidade="baixo",
                        pontos_positivos=[],
                        pontos_negativos=[],
                        resumo="Não foi possível analisar este comentário automaticamente devido a erros na API."
                    ))
                return lote_analises_validadas[:len(lote)]


def analisar_comentarios(comentarios: list[dict]) -> tuple[list[AnaliseIA], dict]:
    """
    Processa a lista de comentários. Busca no cache SQLite e envia em paralelo
    os novos comentários para a IA da OpenRouter.

    Args:
        comentarios: Lista de dicionários com 'id' e 'comentario'.

    Returns:
        Tupla contendo:
        1. Lista de objetos AnaliseIA ordenados correspondentes a cada comentário.
        2. Dicionário com metadados de performance do processamento.
    """
    inicio_tempo = time.time()
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key or api_key == "sua-chave-aqui":
        raise ValueError(
            "Chave da API do OpenRouter não configurada. "
            "Crie um arquivo .env com OPENROUTER_API_KEY=sua-chave"
        )

    total_comentarios = len(comentarios)
    analises_finais = [None] * total_comentarios
    
    comentarios_para_ia = []
    indices_para_ia = []

    # 1. Tentar recuperar do Cache SQLite
    for i, c in enumerate(comentarios):
        comentario_texto = c["comentario"]
        analise_cached = cache_service.buscar_no_cache(comentario_texto)
        if analise_cached:
            analises_finais[i] = analise_cached
        else:
            comentarios_para_ia.append(c)
            indices_para_ia.append(i)

    comentarios_do_cache = total_comentarios - len(comentarios_para_ia)
    comentarios_da_ia = len(comentarios_para_ia)

    # 2. Enviar comentários restantes em lotes paralelos
    if comentarios_para_ia:
        tamanho_lote = 10
        lotes = [
            comentarios_para_ia[x : x + tamanho_lote] 
            for x in range(0, len(comentarios_para_ia), tamanho_lote)
        ]
        total_lotes = len(lotes)
        
        logger.info(
            f"Cache hit: {comentarios_do_cache}/{total_comentarios}. "
            f"Enviando {comentarios_da_ia} novos comentários em {total_lotes} lotes paralelos."
        )

        novas_analises = [None] * len(comentarios_para_ia)

        # Usando ThreadPoolExecutor com limite de 3 threads para processar comentários em paralelo
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(_processar_lote_ia, lotes[l_idx], api_key, l_idx + 1, total_lotes): l_idx
                for l_idx in range(total_lotes)
            }

            for future in concurrent.futures.as_completed(futures):
                l_idx = futures[future]
                try:
                    resultados_lote = future.result()
                    start_pos = l_idx * tamanho_lote
                    for offset, analise_obj in enumerate(resultados_lote):
                        if start_pos + offset < len(novas_analises):
                            novas_analises[start_pos + offset] = analise_obj
                except Exception as e:
                    logger.error(f"Erro crítico no lote {l_idx + 1}: {e}")
                    # Preencher com fallbacks caso o lote inteiro tenha falhado
                    start_pos = l_idx * tamanho_lote
                    tamanho_do_lote = len(lotes[l_idx])
                    for offset in range(tamanho_do_lote):
                        if start_pos + offset < len(novas_analises):
                            novas_analises[start_pos + offset] = AnaliseIA(
                                sentimento="neutro",
                                emocao="indefinido",
                                confianca=0.0,
                                nivel_criticidade="baixo",
                                pontos_positivos=[],
                                pontos_negativos=[],
                                resumo="Erro no processamento deste lote pela IA."
                            )

        # 3. Salvar as novas análises no Cache SQLite
        for c, a in zip(comentarios_para_ia, novas_analises):
            if a:
                cache_service.salvar_no_cache(c["comentario"], a)

        # 4. Inserir nas posições originais da lista final
        for idx, analise_obj in zip(indices_para_ia, novas_analises):
            analises_finais[idx] = analise_obj

    tempo_total = time.time() - inicio_tempo
    tempo_execucao_ms = int(tempo_total * 1000)

    logger.info(
        f"Pipeline de análises concluído em {tempo_total:.2f}s. "
        f"Cache: {comentarios_do_cache} | IA: {comentarios_da_ia}"
    )

    meta_dados = {
        "tempo_execucao_ms": tempo_execucao_ms,
        "total_comentarios": total_comentarios,
        "comentarios_do_cache": comentarios_do_cache,
        "comentarios_da_ia": comentarios_da_ia
    }

    return analises_finais, meta_dados

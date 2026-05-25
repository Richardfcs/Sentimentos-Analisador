"""
data_service.py — Leitura de dados e cálculos estatísticos

Responsável por ler os arquivos JSON de cada categoria, validar os dados,
e calcular as estatísticas gerais e específicas de cada plataforma.
"""

import json
import logging
from pathlib import Path
from collections import Counter, defaultdict
from schemas import (
    AvaliacaoInput,
    AvaliacaoCompleta,
    AnaliseIA,
    EstatisticasGerais,
    PontoRecorrente,
    EvolucaoDiaria,
)

logger = logging.getLogger(__name__)


def carregar_avaliacoes(categoria: str) -> list[AvaliacaoInput]:
    """
    Lê o arquivo JSON da categoria correspondente e valida cada entrada com Pydantic.

    Args:
        categoria: Nome da categoria (ex: playstore, youtube, instagram, amazon).

    Returns:
        Lista de avaliações validadas.

    Raises:
        FileNotFoundError: Se o arquivo não existir.
        ValueError: Se alguma avaliação for inválida.
    """
    caminho = Path(__file__).parent / f"avaliacoes_{categoria}.json"

    if not caminho.exists():
        raise FileNotFoundError(
            f"Arquivo de avaliações não encontrado para a categoria '{categoria}': {caminho}"
        )

    with open(caminho, "r", encoding="utf-8") as f:
        dados_brutos = json.load(f)

    avaliacoes = []
    for i, item in enumerate(dados_brutos):
        try:
            avaliacao = AvaliacaoInput.model_validate(item)
            avaliacoes.append(avaliacao)
        except Exception as e:
            logger.warning(f"Avaliação {i+1} na categoria '{categoria}' inválida e será ignorada: {e}")

    logger.info(f"{len(avaliacoes)} avaliações carregadas e validadas para '{categoria}'")
    return avaliacoes


def calcular_estatisticas(avaliacoes: list[AvaliacaoCompleta], categoria: str) -> EstatisticasGerais:
    """
    Calcula todas as estatísticas gerais (média estrelas, sentimentos) e específicas
    do canal/plataforma em análise.
    """
    total = len(avaliacoes)

    # 1. Estatísticas Gerais Básicas
    media_estrelas = round(
        sum(a.estrelas for a in avaliacoes) / total, 2
    ) if total > 0 else 0.0

    contagem_sentimentos = Counter(a.analise.sentimento for a in avaliacoes)
    contagem_emocoes = Counter(a.analise.emocao for a in avaliacoes)

    # Pontos positivos recorrentes
    todos_positivos = []
    for a in avaliacoes:
        todos_positivos.extend(a.analise.pontos_positivos)
    pontos_pos_counter = Counter(
        p.lower().strip() for p in todos_positivos if p.strip()
    )
    pontos_positivos_recorrentes = [
        PontoRecorrente(ponto=ponto, frequencia=freq)
        for ponto, freq in pontos_pos_counter.most_common(10)
    ]

    # Pontos negativos recorrentes
    todos_negativos = []
    for a in avaliacoes:
        todos_negativos.extend(a.analise.pontos_negativos)
    pontos_neg_counter = Counter(
        p.lower().strip() for p in todos_negativos if p.strip()
    )
    pontos_negativos_recorrentes = [
        PontoRecorrente(ponto=ponto, frequencia=freq)
        for ponto, freq in pontos_neg_counter.most_common(10)
    ]

    # Evolução por data
    evolucao_dict: dict[str, dict[str, int]] = {}
    for a in avaliacoes:
        data_str = a.data.isoformat()
        if data_str not in evolucao_dict:
            evolucao_dict[data_str] = {"positivo": 0, "negativo": 0, "neutro": 0}
        sentimento = a.analise.sentimento
        if sentimento in evolucao_dict[data_str]:
            evolucao_dict[data_str][sentimento] += 1

    evolucao_por_data = [
        EvolucaoDiaria(data=data, **contagens)
        for data, contagens in sorted(evolucao_dict.items())
    ]

    # 2. Métricas Específicas por Plataforma
    metricas_plataforma = {}

    if categoria == "playstore":
        # Sentimento por versão do app
        sent_versao = defaultdict(lambda: {"positivo": 0, "negativo": 0, "neutro": 0, "total": 0, "soma_estrelas": 0})
        for a in avaliacoes:
            if a.versao_app:
                v = a.versao_app
                sent_versao[v][a.analise.sentimento] += 1
                sent_versao[v]["total"] += 1
                sent_versao[v]["soma_estrelas"] += a.estrelas
        
        # Sentimento por versão do Android
        sent_android = defaultdict(lambda: {"positivo": 0, "negativo": 0, "neutro": 0})
        for a in avaliacoes:
            if a.android_version:
                os_v = a.android_version
                sent_android[os_v][a.analise.sentimento] += 1

        metricas_plataforma = {
            "sentimento_por_versao": {
                v: {
                    "positivo": info["positivo"],
                    "negativo": info["negativo"],
                    "neutro": info["neutro"],
                    "total": info["total"],
                    "media_estrelas": round(info["soma_estrelas"] / info["total"], 2) if info["total"] > 0 else 0
                } for v, info in sorted(sent_versao.items())
            },
            "sentimento_por_android": dict(sent_android)
        }

    elif categoria == "youtube":
        # Sentimento por faixa de duração (curto < 10min, médio 10-25min, longo > 25min)
        sent_duracao = {
            "Curto (<10 min)": {"positivo": 0, "negativo": 0, "neutro": 0},
            "Médio (10-25 min)": {"positivo": 0, "negativo": 0, "neutro": 0},
            "Longo (>25 min)": {"positivo": 0, "negativo": 0, "neutro": 0}
        }
        for a in avaliacoes:
            if a.duracao_minutos is not None:
                d = a.duracao_minutos
                faixa = "Curto (<10 min)" if d < 10 else ("Médio (10-25 min)" if d <= 25 else "Longo (>25 min)")
                sent_duracao[faixa][a.analise.sentimento] += 1

        # Sentimento por tema de vídeo (Didática, Áudio, Anúncios, Exemplos)
        sent_tema = defaultdict(lambda: {"positivo": 0, "negativo": 0, "neutro": 0})
        for a in avaliacoes:
            if a.categoria_video:
                t = a.categoria_video
                sent_tema[t][a.analise.sentimento] += 1

        metricas_plataforma = {
            "sentimento_por_duracao": sent_duracao,
            "sentimento_por_tema": dict(sent_tema)
        }

    elif categoria == "instagram":
        # Sentimento por tipo de mídia (reels vs feed post)
        sent_midia = {
            "reels": {"positivo": 0, "negativo": 0, "neutro": 0},
            "post": {"positivo": 0, "negativo": 0, "neutro": 0}
        }
        for a in avaliacoes:
            if a.tipo_midia and a.tipo_midia in sent_midia:
                sent_midia[a.tipo_midia][a.analise.sentimento] += 1

        # Frequência de Hashtags principais e sentimento associado
        sent_tag = defaultdict(lambda: {"positivo": 0, "negativo": 0, "neutro": 0, "total": 0})
        for a in avaliacoes:
            if a.hashtag_principal:
                tag = a.hashtag_principal
                sent_tag[tag][a.analise.sentimento] += 1
                sent_tag[tag]["total"] += 1

        metricas_plataforma = {
            "sentimento_por_midia": sent_midia,
            "sentimento_por_hashtag": {
                tag: {
                    "positivo": info["positivo"],
                    "negativo": info["negativo"],
                    "neutro": info["neutro"],
                    "total": info["total"]
                } for tag, info in sorted(sent_tag.items(), key=lambda x: x[1]["total"], reverse=True)
            }
        }

    elif categoria == "amazon":
        # Média de dias de entrega para cada avaliação por estrelas (1 a 5)
        estrelas_entrega = defaultdict(list)
        for a in avaliacoes:
            if a.dias_entrega is not None:
                estrelas_entrega[a.estrelas].append(a.dias_entrega)
                
        media_entrega_estrelas = {
            str(est): round(sum(dias) / len(dias), 1) if dias else 0.0
            for est in range(1, 6)
            for dias in [estrelas_entrega.get(est, [])]
        }

        # Sentimento relacionado à qualidade de embalagem (excelente, frágil, danificada)
        sent_embalagem = {
            "excelente": {"positivo": 0, "negativo": 0, "neutro": 0},
            "frágil": {"positivo": 0, "negativo": 0, "neutro": 0},
            "danificada": {"positivo": 0, "negativo": 0, "neutro": 0}
        }
        for a in avaliacoes:
            if a.embalagem_status and a.embalagem_status in sent_embalagem:
                sent_embalagem[a.embalagem_status][a.analise.sentimento] += 1

        metricas_plataforma = {
            "media_entrega_por_estrelas": media_entrega_estrelas,
            "sentimento_embalagem": sent_embalagem
        }

    return EstatisticasGerais(
        total_avaliacoes=total,
        media_estrelas=media_estrelas,
        contagem_sentimentos=dict(contagem_sentimentos),
        contagem_emocoes=dict(contagem_emocoes),
        pontos_positivos_recorrentes=pontos_positivos_recorrentes,
        pontos_negativos_recorrentes=pontos_negativos_recorrentes,
        evolucao_por_data=evolucao_por_data,
        metricas_plataforma=metricas_plataforma
    )


def combinar_avaliacoes_com_analises(
    avaliacoes: list[AvaliacaoInput],
    analises: list[AnaliseIA],
) -> list[AvaliacaoCompleta]:
    """
    Combina os dados originais das avaliações com as análises da IA,
    preservando as propriedades específicas de cada plataforma.
    """
    combinadas = []
    for avaliacao, analise in zip(avaliacoes, analises):
        completa = AvaliacaoCompleta(
            id=avaliacao.id,
            usuario=avaliacao.usuario,
            estrelas=avaliacao.estrelas,
            comentario=avaliacao.comentario,
            data=avaliacao.data,
            analise=analise,
            versao_app=avaliacao.versao_app,
            android_version=avaliacao.android_version,
            duracao_minutos=avaliacao.duracao_minutos,
            categoria_video=avaliacao.categoria_video,
            tipo_midia=avaliacao.tipo_midia,
            hashtag_principal=avaliacao.hashtag_principal,
            dias_entrega=avaliacao.dias_entrega,
            embalagem_status=avaliacao.embalagem_status,
        )
        combinadas.append(completa)

    logger.info(f"{len(combinadas)} avaliações combinadas com análises da IA")
    return combinadas

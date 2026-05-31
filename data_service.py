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
    InsightItem,
    ActionStepItem,
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


PLANOS_ACAO = {
    "playstore": [
        ActionStepItem(passo=1, titulo="Corrigir Travamento da V2.1.2 no Android 12", descricao="Resolver bug de permissão de notificação e reverter o patch de sincronização em segundo plano imediatamente.", prioridade="alta"),
        ActionStepItem(passo=2, titulo="Otimizar Processo de Autenticação", descricao="Refatorar o fluxo de login lento relatado por usuários após a última atualização de segurança.", prioridade="media"),
        ActionStepItem(passo=3, titulo="Expandir Tema Escuro", descricao="Implementar a interface escura em 100% das telas secundárias após feedback altamente positivo de 30% dos usuários.", prioridade="baixa"),
    ],
    "youtube": [
        ActionStepItem(passo=1, titulo="Reduzir Propagandas Mid-Roll em Vídeos Longos", descricao="Dividir vídeos acima de 25 minutos em partes ou otimizar a inserção de anúncios automáticos para reduzir rejeição de 35%.", prioridade="alta"),
        ActionStepItem(passo=2, titulo="Tratamento de Áudio e Ruído", descricao="Implementar filtro de redução de ruído nos próximos tutoriais para reverter a queda de 12% na taxa de retenção.", prioridade="media"),
        ActionStepItem(passo=3, titulo="Dobrar Foco em Tutoriais de Código", descricao="Aumentar a frequência de postagem de vídeos práticos e didáticos que alcançaram aprovação unânime de 95%.", prioridade="baixa"),
    ],
    "instagram": [
        ActionStepItem(passo=1, titulo="Priorizar Reels Educacionais Curtos", descricao="Focar 80% do conteúdo criativo em Reels dinâmicos de até 30 segundos, impulsionando sentimentos de gratidão.", prioridade="alta"),
        ActionStepItem(passo=2, titulo="Limpeza de Hashtags Irrelevantes", descricao="Substituir hashtags genéricas (como #dev) por tags de caixas de perguntas e engajamento orgânico de comunidade.", prioridade="media"),
        ActionStepItem(passo=3, titulo="Otimizar Resolução de Upload de Reels", descricao="Corrigir bugs de falha de reprodução comprimindo vídeos de forma nativa para evitar quebra no player.", prioridade="baixa"),
    ],
    "amazon": [
        ActionStepItem(passo=1, titulo="Resolver Atrasos Críticos de Logística", descricao="Substituir o parceiro logístico regional nas rotas onde as entregas ultrapassam 5 dias úteis.", prioridade="alta"),
        ActionStepItem(passo=2, titulo="Reforço e Padrão de Embalagem", descricao="Priorizar embalagens reforçadas para itens rotulados como frágeis para eliminar sentimentos de raiva e frustração.", prioridade="media"),
        ActionStepItem(passo=3, titulo="Alavancar Entregas Expressas", descricao="Oferecer frete rápido com surpresa de 2 dias de prazo para clientes fiéis, estimulando reviews positivos.", prioridade="baixa"),
    ],
}


def calcular_estatisticas(avaliacoes: list[AvaliacaoCompleta], categoria: str) -> EstatisticasGerais:
    """
    Calcula todas as estatísticas gerais (média estrelas, sentimentos) e específicas
    do canal/plataforma em análise.
    """
    total = len(avaliacoes)

    # 1. Estatísticas Gerais Básicas
    valid_estrelas = [a.estrelas for a in avaliacoes if a.estrelas is not None]
    media_estrelas = round(sum(valid_estrelas) / len(valid_estrelas), 2) if valid_estrelas else None

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

        # Média de curtidas e compartilhamentos
        curtidas_validas = [a.curtidas for a in avaliacoes if a.curtidas is not None]
        compartilhamentos_validos = [a.compartilhamentos for a in avaliacoes if a.compartilhamentos is not None]
        media_curtidas = round(sum(curtidas_validas) / len(curtidas_validas), 1) if curtidas_validas else 0.0
        media_compartilhamentos = round(sum(compartilhamentos_validos) / len(compartilhamentos_validos), 1) if compartilhamentos_validos else 0.0

        metricas_plataforma = {
            "media_curtidas": media_curtidas,
            "media_compartilhamentos": media_compartilhamentos,
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

        # Média de curtidas e compartilhamentos
        curtidas_validas = [a.curtidas for a in avaliacoes if a.curtidas is not None]
        compartilhamentos_validos = [a.compartilhamentos for a in avaliacoes if a.compartilhamentos is not None]
        media_curtidas = round(sum(curtidas_validas) / len(curtidas_validas), 1) if curtidas_validas else 0.0
        media_compartilhamentos = round(sum(compartilhamentos_validos) / len(compartilhamentos_validos), 1) if compartilhamentos_validos else 0.0

        metricas_plataforma = {
            "media_curtidas": media_curtidas,
            "media_compartilhamentos": media_compartilhamentos,
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

    # 3. Insights da IA
    insights = []
    if categoria == "playstore":
        insights = [
            InsightItem(texto="A versão 2.1.2 do aplicativo apresentou um aumento de 40% nas reclamações de travamentos de tela em aparelhos com Android 12.", tipo="alerta", is_premium=False),
            InsightItem(texto="Os elogios sobre a nova interface escura cresceram 30% em comparação com as versões anteriores.", tipo="sucesso", is_premium=False),
            InsightItem(texto="Reclamações sobre a lentidão da tela de login após a última autenticação de segurança do console do Google Play.", tipo="info", is_premium=False),
            InsightItem(texto="Análise de correlação indica que usuários de Android 13 são 2.5x mais propensos a dar reviews de 1 estrela devido ao bug de permissão de notificação.", tipo="alerta", is_premium=True),
            InsightItem(texto="Sugestão: Reverter patch de sincronização em segundo plano ou adicionar tratamento de exceção explícito para APIs do Android 12+.", tipo="sugestao", is_premium=True)
        ]
    elif categoria == "youtube":
        insights = [
            InsightItem(texto="Vídeos com duração acima de 25 minutos têm taxa de desengajamento e sentimento negativo 35% maior devido ao excesso de anúncios mid-roll.", tipo="alerta", is_premium=False),
            InsightItem(texto="Tutoriais práticos com exemplos de código possuem aprovação unânime de 95% de satisfação do público.", tipo="sucesso", is_premium=False),
            InsightItem(texto="Vlogs Semanais e conteúdos de opinião apresentam maior oscilação emocional (neutros/duvidosos aumentam em 45%).", tipo="info", is_premium=False),
            InsightItem(texto="Correlação identificada: Problemas de ruído de áudio nos últimos 3 vídeos de tutoriais resultaram em queda de 12% na taxa de retenção média.", tipo="alerta", is_premium=True),
            InsightItem(texto="Recomendação estratégica: Dividir os vídeos longos em partes de no máximo 15 minutos ou otimizar a inserção automática de propagandas.", tipo="sugestao", is_premium=True)
        ]
    elif categoria == "instagram":
        insights = [
            InsightItem(texto="Reels de conteúdo educacional geram 3x mais sentimentos de gratidão e confiança que posts estáticos no feed.", tipo="sucesso", is_premium=False),
            InsightItem(texto="Hashtags genéricas (como #dev) atraem comentários robóticos ou neutros, poluindo a análise de audiência real.", tipo="info", is_premium=False),
            InsightItem(texto="Reclamações de falhas na reprodução de vídeos nos Reels de alta resolução reportadas em posts recentes.", tipo="alerta", is_premium=False),
            InsightItem(texto="Análise de tráfego orgânico demonstra que posts contendo caixas de perguntas aumentam a emoção de proximidade/satisfação em 70%.", tipo="sucesso", is_premium=True),
            InsightItem(texto="Sugestão de branding: Direcionar 80% do orçamento criativo para produção de Reels dinâmicos de até 30 segundos usando a hashtag principal.", tipo="sugestao", is_premium=True)
        ]
    elif categoria == "amazon":
        insights = [
            InsightItem(texto="Atrasos na entrega acima de 5 dias úteis derrubam a avaliação média para 1.8 estrelas, independentemente da qualidade do produto.", tipo="alerta", is_premium=False),
            InsightItem(texto="A embalagem rotulada como 'Danificada' está fortemente relacionada a sentimentos de raiva e frustração (representando 85% dessas menções).", tipo="alerta", is_premium=False),
            InsightItem(texto="Produtos entregues na embalagem 'Excelente' têm índice de satisfação 2x maior e 40% mais menções espontâneas elogiosas.", tipo="sucesso", is_premium=False),
            InsightItem(texto="Clientes que receberam o produto em até 2 dias úteis demonstraram sentimento de surpresa positiva e lealdade alta (grau de confiança de 98% da IA).", tipo="sucesso", is_premium=True),
            InsightItem(texto="Ação recomendada: Substituir parceiro logístico regional nas rotas onde as embalagens chegam danificadas e priorizar embalagens reforçadas para itens frágeis.", tipo="sugestao", is_premium=True)
        ]

    return EstatisticasGerais(
        total_avaliacoes=total,
        media_estrelas=media_estrelas,
        contagem_sentimentos=dict(contagem_sentimentos),
        contagem_emocoes=dict(contagem_emocoes),
        pontos_positivos_recorrentes=pontos_positivos_recorrentes,
        pontos_negativos_recorrentes=pontos_negativos_recorrentes,
        evolucao_por_data=evolucao_por_data,
        insights=insights,
        plano_acao=PLANOS_ACAO.get(categoria, []),
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
            curtidas=avaliacao.curtidas,
            compartilhamentos=avaliacao.compartilhamentos,
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

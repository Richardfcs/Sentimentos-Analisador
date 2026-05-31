"""
schemas.py — Modelos Pydantic para validação de dados

Define as estruturas de entrada (JSON de avaliações) e saída (resposta da IA),
garantindo tipagem e validação consistentes em todo o sistema.
"""

from pydantic import BaseModel, Field
from typing import Literal
from datetime import date


class AvaliacaoInput(BaseModel):
    """Modelo para validar cada avaliação do arquivo JSON específico."""
    id: int
    usuario: str
    estrelas: int | None = Field(default=None, ge=1, le=5, description="Nota de 1 a 5 estrelas")
    comentario: str = Field(min_length=5, description="Comentário textual do usuário")
    data: date

    # Campos de engajamento social (YouTube, Instagram)
    curtidas: int | None = None
    compartilhamentos: int | None = None

    # Campos opcionais para as diferentes plataformas
    versao_app: str | None = None
    android_version: str | None = None
    duracao_minutos: int | None = None
    categoria_video: str | None = None
    tipo_midia: str | None = None
    hashtag_principal: str | None = None
    dias_entrega: int | None = None
    embalagem_status: str | None = None


class AnaliseIA(BaseModel):
    """Modelo para validar a resposta da IA para cada comentário analisado."""
    sentimento: Literal["positivo", "negativo", "neutro"]
    emocao: str = Field(description="Ex: satisfacao, frustracao, raiva, confianca, duvida, surpresa, gratidao, decepcao")
    confianca: float = Field(ge=0.0, le=1.0, description="Nível de confiança da classificação (0 a 1)")
    nivel_criticidade: Literal["baixo", "medio", "alto"]
    pontos_positivos: list[str] = Field(default_factory=list, description="Aspectos elogiados pelo usuário")
    pontos_negativos: list[str] = Field(default_factory=list, description="Problemas citados pelo usuário")
    resumo: str = Field(description="Resumo curto do sentimento da avaliação")


class AvaliacaoCompleta(BaseModel):
    """Combina os dados originais da avaliação com a análise feita pela IA."""
    id: int
    usuario: str
    estrelas: int | None = None
    comentario: str
    data: date
    analise: AnaliseIA

    # Campos de engajamento social
    curtidas: int | None = None
    compartilhamentos: int | None = None

    # Campos específicos das plataformas
    versao_app: str | None = None
    android_version: str | None = None
    duracao_minutos: int | None = None
    categoria_video: str | None = None
    tipo_midia: str | None = None
    hashtag_principal: str | None = None
    dias_entrega: int | None = None
    embalagem_status: str | None = None


class PontoRecorrente(BaseModel):
    """Representa um ponto positivo ou negativo com sua frequência."""
    ponto: str
    frequencia: int


class EvolucaoDiaria(BaseModel):
    """Contagem de sentimentos por data para gráfico de evolução."""
    data: str
    positivo: int = 0
    negativo: int = 0
    neutro: int = 0


class InsightItem(BaseModel):
    """Representa um insight acionável gerado pelo sistema."""
    texto: str
    tipo: Literal["alerta", "sucesso", "sugestao", "info"]
    is_premium: bool = False


class ActionStepItem(BaseModel):
    """Representa uma etapa do roteiro de ação gerado pela IA."""
    passo: int
    titulo: str
    descricao: str
    prioridade: Literal["alta", "media", "baixa"]
    is_premium: bool = True


class EstatisticasGerais(BaseModel):
    """Estatísticas calculadas pelo backend (não pela IA)."""
    total_avaliacoes: int
    media_estrelas: float | None
    contagem_sentimentos: dict[str, int]
    contagem_emocoes: dict[str, int]
    pontos_positivos_recorrentes: list[PontoRecorrente]
    pontos_negativos_recorrentes: list[PontoRecorrente]
    evolucao_por_data: list[EvolucaoDiaria]
    insights: list[InsightItem] = Field(default_factory=list)
    plano_acao: list[ActionStepItem] = Field(default_factory=list)
    
    # Métricas dinâmicas calculadas de acordo com a categoria selecionada
    metricas_plataforma: dict = Field(default_factory=dict)

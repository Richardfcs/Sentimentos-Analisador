import pytest
from datetime import date
from pydantic import ValidationError
from schemas import AvaliacaoInput, AnaliseIA, InsightItem, ActionStepItem, EstatisticasGerais

def test_avaliacao_input_valid():
    """Valida que uma avaliação correta é aceita pelo schema."""
    data = {
        "id": 1,
        "usuario": "Test User",
        "estrelas": 5,
        "comentario": "Este é um comentário válido de teste.",
        "data": "2026-06-01"
    }
    obj = AvaliacaoInput.model_validate(data)
    assert obj.id == 1
    assert obj.usuario == "Test User"
    assert obj.estrelas == 5
    assert obj.comentario == "Este é um comentário válido de teste."
    assert obj.data == date(2026, 6, 1)

def test_avaliacao_input_optional_stars():
    """Valida que estrelas=None é aceito para redes sociais."""
    data = {
        "id": 2,
        "usuario": "Social User",
        "estrelas": None,
        "comentario": "Vídeo excelente, muito bom engajamento!",
        "data": "2026-06-02",
        "curtidas": 250,
        "compartilhamentos": 15
    }
    obj = AvaliacaoInput.model_validate(data)
    assert obj.estrelas is None
    assert obj.curtidas == 250
    assert obj.compartilhamentos == 15

def test_avaliacao_input_stars_limits():
    """Valida que notas fora do intervalo 1-5 geram erro de validação."""
    base_data = {
        "id": 1,
        "usuario": "User",
        "comentario": "Comentário de teste.",
        "data": "2026-06-01"
    }
    
    # Menor que 1
    with pytest.raises(ValidationError):
        AvaliacaoInput.model_validate({**base_data, "estrelas": 0})
        
    # Maior que 5
    with pytest.raises(ValidationError):
        AvaliacaoInput.model_validate({**base_data, "estrelas": 6})

def test_avaliacao_input_comment_too_short():
    """Valida que comentário com menos de 5 caracteres gera erro de validação."""
    data = {
        "id": 1,
        "usuario": "User",
        "estrelas": 3,
        "comentario": "Ola", # Menor que 5 caracteres
        "data": "2026-06-01"
    }
    with pytest.raises(ValidationError):
        AvaliacaoInput.model_validate(data)

def test_analise_ia_valid():
    """Valida o schema da análise da IA com dados corretos."""
    data = {
        "sentimento": "positivo",
        "emocao": "satisfacao",
        "confianca": 0.95,
        "nivel_criticidade": "baixo",
        "pontos_positivos": ["rapidez", "atendimento"],
        "pontos_negativos": [],
        "resumo": "Excelente serviço prestado."
    }
    obj = AnaliseIA.model_validate(data)
    assert obj.sentimento == "positivo"
    assert obj.emocao == "satisfacao"
    assert obj.confianca == 0.95
    assert obj.nivel_criticidade == "baixo"
    assert len(obj.pontos_positivos) == 2

def test_analise_ia_invalid_sentimento():
    """Garante erro de validação se sentimento não estiver na lista permitida."""
    data = {
        "sentimento": "feliz", # Inválido (deve ser positivo, negativo ou neutro)
        "emocao": "satisfacao",
        "confianca": 0.9,
        "nivel_criticidade": "baixo",
        "pontos_positivos": [],
        "pontos_negativos": [],
        "resumo": "Resumo"
    }
    with pytest.raises(ValidationError):
        AnaliseIA.model_validate(data)

def test_analise_ia_invalid_confianca():
    """Garante erro de validação para confiança fora dos limites [0.0, 1.0]."""
    base = {
        "sentimento": "positivo",
        "emocao": "satisfacao",
        "nivel_criticidade": "baixo",
        "pontos_positivos": [],
        "pontos_negativos": [],
        "resumo": "Resumo"
    }
    with pytest.raises(ValidationError):
        AnaliseIA.model_validate({**base, "confianca": -0.1})
    with pytest.raises(ValidationError):
        AnaliseIA.model_validate({**base, "confianca": 1.1})

def test_insight_item_valid():
    """Garante validação correta de itens de insight."""
    data = {"texto": "Insight 1", "tipo": "sucesso", "is_premium": False}
    obj = InsightItem.model_validate(data)
    assert obj.tipo == "sucesso"
    assert not obj.is_premium

    with pytest.raises(ValidationError):
        # Tipo inválido
        InsightItem.model_validate({"texto": "Insight", "tipo": "invalido"})

def test_action_step_item_valid():
    """Garante validação correta de passos do plano de ação."""
    data = {
        "passo": 1,
        "titulo": "Passo 1",
        "descricao": "Fazer X e Y",
        "prioridade": "alta"
    }
    obj = ActionStepItem.model_validate(data)
    assert obj.passo == 1
    assert obj.prioridade == "alta"
    assert obj.is_premium is True # Default

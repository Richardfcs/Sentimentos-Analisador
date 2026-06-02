import pytest
import json
from unittest.mock import patch
from schemas import AnaliseIA

# Mock da função de análise de comentários para as rotas do Flask
def obter_analise_mockada(comentarios):
    analises = []
    for c in comentarios:
        analises.append(AnaliseIA(
            sentimento="positivo",
            emocao="satisfacao",
            confianca=0.95,
            nivel_criticidade="baixo",
            pontos_positivos=["bom"],
            pontos_negativos=[],
            resumo="Análise mockada do app."
        ))
    meta = {
        "tempo_execucao_ms": 25,
        "total_comentarios": len(comentarios),
        "comentarios_do_cache": 0,
        "comentarios_da_ia": len(comentarios)
    }
    return analises, meta

@pytest.fixture(autouse=True)
def mock_flask_ai_service():
    """Intercepa todas as chamadas de IA do app.py para rodar localmente sem rede."""
    with patch("app.analisar_comentarios", side_effect=obter_analise_mockada) as mock:
        yield mock

def test_index_route(client):
    """Garante que a rota raiz / carrega com sucesso e renderiza a casca HTML."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "<title>Analisador de Sentimentos com IA</title>" in html
    assert "SentView" in html

def test_api_dados_valid_category(client):
    """Garante que a rota de dados do dashboard carrega dados válidos (ex: Play Store)."""
    response = client.get("/api/dados/playstore")
    assert response.status_code == 200
    
    data = json.loads(response.data.decode("utf-8"))
    assert "avaliacoes" in data
    assert "estatisticas" in data
    assert "performance" in data
    
    assert len(data["avaliacoes"]) == 100
    assert data["avaliacoes"][0]["usuario"] is not None
    assert data["estatisticas"]["total_avaliacoes"] == 100

def test_api_dados_invalid_category(client):
    """Garante erro 400 ao tentar carregar dados de categoria inválida."""
    response = client.get("/api/dados/categoria_inexistente")
    assert response.status_code == 400
    
    data = json.loads(response.data.decode("utf-8"))
    assert "erro" in data
    assert "Categoria inválida" in data["erro"]

def test_api_dados_with_simulation_params(client):
    """Garante que parâmetros de simulação de conexão de API funcionam."""
    response = client.get("/api/dados/youtube?target_id=https://youtube.com/watch?v=123&api_key=AIzaSySecret")
    assert response.status_code == 200
    
    data = json.loads(response.data.decode("utf-8"))
    assert len(data["avaliacoes"]) == 100

def test_api_analisar_avulso_success(client):
    """Garante que a Sandbox analisa corretamente um comentário válido."""
    payload = {"texto": "Produto fantástico! Funciona muito bem e o suporte é sensacional."}
    response = client.post(
        "/api/analisar-avulso",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    
    data = json.loads(response.data.decode("utf-8"))
    assert data["sentimento"] == "positivo"
    assert data["emocao"] == "satisfacao"
    assert data["confianca"] == 0.95

def test_api_analisar_avulso_invalid_payload(client):
    """Garante erro 400 se o payload da Sandbox for vazio ou sem o campo 'texto'."""
    # Caso 1: sem campo 'texto'
    response1 = client.post(
        "/api/analisar-avulso",
        data=json.dumps({}),
        content_type="application/json"
    )
    assert response1.status_code == 400
    
    # Caso 2: texto em branco ou somente espaços
    response2 = client.post(
        "/api/analisar-avulso",
        data=json.dumps({"texto": "   "}),
        content_type="application/json"
    )
    assert response2.status_code == 400

def test_api_limpar_cache(client):
    """Valida limpeza geral do cache via requisição de API."""
    response = client.post("/api/limpar-cache")
    assert response.status_code == 200
    
    data = json.loads(response.data.decode("utf-8"))
    assert "mensagem" in data
    assert "caches" in data["mensagem"]

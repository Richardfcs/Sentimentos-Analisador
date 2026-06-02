import pytest
import time
from unittest.mock import patch, MagicMock
import ai_service
import cache_service
from schemas import AnaliseIA

def test_extrair_json_da_resposta_direto():
    """Valida extração simples de JSON."""
    texto = '[{"sentimento": "positivo", "emocao": "satisfacao", "confianca": 0.9, "nivel_criticidade": "baixo", "pontos_positivos": [], "pontos_negativos": [], "resumo": "Excelente"}]'
    res = ai_service._extrair_json_da_resposta(texto)
    assert len(res) == 1
    assert res[0]["sentimento"] == "positivo"

def test_extrair_json_da_resposta_com_texto():
    """Valida extração de JSON cercado de explicações."""
    texto = 'Olá humano. Aqui está a resposta:\n\n[{"sentimento": "negativo", "emocao": "raiva", "confianca": 0.95, "nivel_criticidade": "alto", "pontos_positivos": [], "pontos_negativos": ["ruim"], "resumo": "Ruim"}]\n\nEspero ter ajudado!'
    res = ai_service._extrair_json_da_resposta(texto)
    assert len(res) == 1
    assert res[0]["sentimento"] == "negativo"

def test_extrair_json_da_resposta_markdown():
    """Valida extração de JSON de dentro de blocos markdown ```json."""
    texto = '```json\n[{"sentimento": "neutro", "emocao": "duvida", "confianca": 0.8, "nivel_criticidade": "baixo", "pontos_positivos": [], "pontos_negativos": [], "resumo": "Ok"}]\n```'
    res = ai_service._extrair_json_da_resposta(texto)
    assert len(res) == 1
    assert res[0]["sentimento"] == "neutro"

def test_extrair_json_da_resposta_invalido():
    """Garante ValueError caso não haja formato JSON detectável."""
    with pytest.raises(ValueError):
        ai_service._extrair_json_da_resposta("Este texto não contém nenhum formato JSON em array.")

@patch("ai_service.requests.post")
def test_analisar_comentarios_api_key_missing(mock_post, monkeypatch):
    """Garante erro de validação caso a chave OpenRouter não esteja no ambiente."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ValueError) as excinfo:
        ai_service.analisar_comentarios([{"id": 1, "comentario": "comentario"}])
    assert "Chave da API" in str(excinfo.value)

@patch("ai_service.requests.post")
@patch("ai_service.time.sleep")
def test_analisar_comentarios_sucesso(mock_sleep, mock_post):
    """Valida fluxo de sucesso com chamada à API e gravação automática no cache SQLite."""
    # Configura mock do requests
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": '[{"sentimento": "positivo", "emocao": "satisfacao", "confianca": 0.99, "nivel_criticidade": "baixo", "pontos_positivos": ["bom"], "pontos_negativos": [], "resumo": "Excelente"}]'
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    comentarios = [{"id": 101, "comentario": "Este produto e muito bom!"}]
    
    # 1. Primeira chamada: Cache Miss, bate na API
    analises, meta = ai_service.analisar_comentarios(comentarios)
    assert len(analises) == 1
    assert analises[0].sentimento == "positivo"
    assert meta["comentarios_do_cache"] == 0
    assert meta["comentarios_da_ia"] == 1
    mock_post.assert_called_once()
    
    # 2. Segunda chamada idêntica: Cache Hit, não deve bater na API
    mock_post.reset_mock()
    analises_cached, meta_cached = ai_service.analisar_comentarios(comentarios)
    assert len(analises_cached) == 1
    assert analises_cached[0].sentimento == "positivo"
    assert meta_cached["comentarios_do_cache"] == 1
    assert meta_cached["comentarios_da_ia"] == 0
    mock_post.assert_not_called()

@patch("ai_service.requests.post")
def test_analisar_comentarios_erro_402_pagamento(mock_post):
    """Valida comportamento e mensagens do erro 402 (Payment Required)."""
    mock_response = MagicMock()
    mock_response.status_code = 402
    mock_post.return_value = mock_response
    
    comentarios = [{"id": 1, "comentario": "comentario de teste"}]
    
    # O erro 402 deve interromper imediatamente e falhar o lote, disparando fallback
    analises, meta = ai_service.analisar_comentarios(comentarios)
    assert len(analises) == 1
    assert analises[0].sentimento == "neutro"
    assert "Não foi possível analisar" in analises[0].resumo

@patch("ai_service.requests.post")
@patch("ai_service.time.sleep")
def test_analisar_comentarios_fallback_apos_retry(mock_sleep, mock_post):
    """Garante que falhas sucessivas (ex: erro 500) ativam o fallback após esgotar tentativas."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = Exception("Internal Server Error")
    mock_post.return_value = mock_response
    
    comentarios = [{"id": 1, "comentario": "comentario ruim"}]
    
    analises, meta = ai_service.analisar_comentarios(comentarios)
    assert len(analises) == 1
    assert analises[0].sentimento == "neutro"
    assert analises[0].emocao == "indefinido"
    assert "Não foi possível analisar" in analises[0].resumo
    
    # 3 tentativas configuradas
    assert mock_post.call_count == 3

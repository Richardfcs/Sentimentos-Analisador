import pytest
import os
import cache_service
from pathlib import Path
from app import app as flask_app

@pytest.fixture(autouse=True)
def mock_db_path(tmp_path):
    """Garante que todos os testes rodem em um banco de dados SQLite temporário e isolado."""
    temp_db = tmp_path / "test_cache.db"
    original_db = cache_service.DB_PATH
    cache_service.DB_PATH = temp_db
    
    # Inicializa o banco de dados temporário
    cache_service.inicializar_banco()
    
    yield temp_db
    
    # Restaura o caminho do banco original
    cache_service.DB_PATH = original_db

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Define variáveis de ambiente mockadas para evitar erros de validação ou de rede."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "mock-api-key-sentview-123")

@pytest.fixture
def client():
    """Retorna um cliente de teste do Flask configurado em modo TESTING."""
    flask_app.config.update({
        "TESTING": True,
    })
    # Limpa cache em memória do Flask antes de rodar os testes
    from app import _cache_dados
    _cache_dados.clear()
    
    with flask_app.test_client() as test_client:
        yield test_client

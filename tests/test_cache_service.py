import pytest
import sqlite3
import cache_service
from schemas import AnaliseIA

def test_obter_hash_comentario():
    """Garante que a normalização de texto e geração de hash sha256 funcionam corretamente."""
    c1 = "  Excelente aplicativo, recomendo!  "
    c2 = "excelente aplicativo, recomendo!"
    
    hash1 = cache_service.obter_hash_comentario(c1)
    hash2 = cache_service.obter_hash_comentario(c2)
    
    # Devem produzir o mesmo hash (strip + lower)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 em hexadecimal tem 64 caracteres

def test_cache_miss_returns_none():
    """Garante que buscar um comentário inexistente no cache retorna None."""
    resultado = cache_service.buscar_no_cache("Este comentário nunca foi visto antes.")
    assert resultado is None

def test_salvar_e_buscar_no_cache():
    """Valida o fluxo completo de escrita e leitura no cache SQLite."""
    comentario = "O aplicativo é muito bom, mas trava às vezes."
    analise = AnaliseIA(
        sentimento="positivo",
        emocao="satisfacao",
        confianca=0.85,
        nivel_criticidade="baixo",
        pontos_positivos=["muito bom"],
        pontos_negativos=["trava as vezes"],
        resumo="Muito bom, mas trava."
    )
    
    # Salva no cache
    cache_service.salvar_no_cache(comentario, analise)
    
    # Busca de volta
    cached_analise = cache_service.buscar_no_cache(comentario)
    
    # Verifica equivalência
    assert cached_analise is not None
    assert cached_analise.sentimento == "positivo"
    assert cached_analise.emocao == "satisfacao"
    assert cached_analise.confianca == 0.85
    assert cached_analise.nivel_criticidade == "baixo"
    assert cached_analise.pontos_positivos == ["muito bom"]
    assert cached_analise.pontos_negativos == ["trava as vezes"]
    assert cached_analise.resumo == "Muito bom, mas trava."

def test_limpar_cache_completo():
    """Valida que a limpeza remove todos os dados da tabela de cache."""
    comentario = "Comentário de teste para limpeza."
    analise = AnaliseIA(
        sentimento="neutro",
        emocao="duvida",
        confianca=0.5,
        nivel_criticidade="baixo",
        pontos_positivos=[],
        pontos_negativos=[],
        resumo="Neutro."
    )
    
    # Salva
    cache_service.salvar_no_cache(comentario, analise)
    assert cache_service.buscar_no_cache(comentario) is not None
    
    # Limpa
    cache_service.limpar_cache_completo()
    
    # Deve ser None agora
    assert cache_service.buscar_no_cache(comentario) is None

import pytest
from pathlib import Path
import data_service
from schemas import AvaliacaoInput, AnaliseIA, AvaliacaoCompleta
from datetime import date

def test_carregar_avaliacoes_valid_categories():
    """Garante que as avaliações de todas as 4 categorias válidas carregam exatamente 100 registros."""
    for cat in ["playstore", "youtube", "instagram", "amazon"]:
        avaliacoes = data_service.carregar_avaliacoes(cat)
        assert isinstance(avaliacoes, list)
        assert len(avaliacoes) == 100
        for item in avaliacoes:
            assert isinstance(item, AvaliacaoInput)

def test_carregar_avaliacoes_invalid_category():
    """Garante FileNotFoundError ao passar categoria inválida."""
    with pytest.raises(FileNotFoundError):
        data_service.carregar_avaliacoes("plataforma_invalida")

def test_combinar_avaliacoes_com_analises():
    """Valida o emparelhamento correto entre avaliações de entrada e respostas da IA."""
    av_input = [
        AvaliacaoInput(id=1, usuario="User 1", comentario="Muito bom", data=date(2026, 6, 1))
    ]
    analises = [
        AnaliseIA(
            sentimento="positivo",
            emocao="satisfacao",
            confianca=0.9,
            nivel_criticidade="baixo",
            pontos_positivos=["muito bom"],
            pontos_negativos=[],
            resumo="Positivo"
        )
    ]
    
    combinadas = data_service.combinar_avaliacoes_com_analises(av_input, analises)
    
    assert len(combinadas) == 1
    assert isinstance(combinadas[0], AvaliacaoCompleta)
    assert combinadas[0].id == 1
    assert combinadas[0].usuario == "User 1"
    assert combinadas[0].analise.sentimento == "positivo"

def _obter_dados_combinados_mockados(categoria, sentimento="positivo", emocao="satisfacao", estrelas=5, curtidas=100):
    """Auxiliar para gerar avaliações completas mockadas."""
    avaliacoes = []
    for i in range(10):
        # Diferentes datas para verificar evolução
        dia = 1 + (i % 3)
        data_obj = date(2026, 5, dia)
        
        analise = AnaliseIA(
            sentimento=sentimento,
            emocao=emocao,
            confianca=0.85,
            nivel_criticidade="baixo",
            pontos_positivos=["bom"],
            pontos_negativos=[],
            resumo="Tudo certo."
        )
        
        avaliacoes.append(AvaliacaoCompleta(
            id=i+1,
            usuario=f"Usuario {i}",
            estrelas=estrelas if categoria in ["playstore", "amazon"] else None,
            comentario="Comentário mockado de teste.",
            data=data_obj,
            analise=analise,
            curtidas=curtidas if categoria in ["youtube", "instagram"] else None,
            compartilhamentos=10 if categoria in ["youtube", "instagram"] else None,
            versao_app="2.1.2" if categoria == "playstore" else None,
            android_version="Android 12" if categoria == "playstore" else None,
            duracao_minutos=15 if categoria == "youtube" else None,
            categoria_video="Didática" if categoria == "youtube" else None,
            tipo_midia="reels" if categoria == "instagram" else None,
            hashtag_principal="#branding" if categoria == "instagram" else None,
            dias_entrega=3 if categoria == "amazon" else None,
            embalagem_status="excelente" if categoria == "amazon" else None
        ))
    return avaliacoes

def test_calcular_estatisticas_playstore():
    """Valida agregação de estatísticas para a Google Play Store (estrelas, Android, versão)."""
    avaliacoes = _obter_dados_combinados_mockados("playstore", sentimento="positivo", estrelas=5)
    stats = data_service.calcular_estatisticas(avaliacoes, "playstore")
    
    assert stats.total_avaliacoes == 10
    assert stats.media_estrelas == 5.0
    assert stats.contagem_sentimentos["positivo"] == 10
    
    # Métricas Play Store
    metrics = stats.metricas_plataforma
    assert "sentimento_por_versao" in metrics
    assert "sentimento_por_android" in metrics
    assert metrics["sentimento_por_versao"]["2.1.2"]["total"] == 10
    assert metrics["sentimento_por_versao"]["2.1.2"]["media_estrelas"] == 5.0
    assert metrics["sentimento_por_android"]["Android 12"]["positivo"] == 10
    
    # Insights/Planos
    assert len(stats.insights) > 0
    assert len(stats.plano_acao) == 3
    assert stats.plano_acao[0].titulo == "Corrigir Travamento da V2.1.2 no Android 12"

def test_calcular_estatisticas_youtube():
    """Valida agregação de estatísticas do YouTube (Likes, faixa duração, categoria)."""
    avaliacoes = _obter_dados_combinados_mockados("youtube", sentimento="negativo", emocao="frustracao", curtidas=50)
    stats = data_service.calcular_estatisticas(avaliacoes, "youtube")
    
    assert stats.total_avaliacoes == 10
    assert stats.media_estrelas is None
    
    metrics = stats.metricas_plataforma
    assert metrics["media_curtidas"] == 50.0
    assert metrics["media_compartilhamentos"] == 10.0
    assert metrics["sentimento_por_duracao"]["Médio (10-25 min)"]["negativo"] == 10
    assert metrics["sentimento_por_tema"]["Didática"]["negativo"] == 10

def test_calcular_estatisticas_instagram():
    """Valida agregação de estatísticas do Instagram (Likes, Reels vs Feed, Hashtags)."""
    avaliacoes = _obter_dados_combinados_mockados("instagram", sentimento="positivo", curtidas=200)
    stats = data_service.calcular_estatisticas(avaliacoes, "instagram")
    
    metrics = stats.metricas_plataforma
    assert metrics["media_curtidas"] == 200.0
    assert metrics["sentimento_por_midia"]["reels"]["positivo"] == 10
    assert metrics["sentimento_por_hashtag"]["#branding"]["total"] == 10

def test_calcular_estatisticas_amazon():
    """Valida agregação de estatísticas da Amazon (prazo de entrega, embalagem)."""
    avaliacoes = _obter_dados_combinados_mockados("amazon", sentimento="neutro", estrelas=3)
    stats = data_service.calcular_estatisticas(avaliacoes, "amazon")
    
    assert stats.media_estrelas == 3.0
    metrics = stats.metricas_plataforma
    assert metrics["media_entrega_por_estrelas"]["3"] == 3.0
    assert metrics["sentimento_embalagem"]["excelente"]["neutro"] == 10

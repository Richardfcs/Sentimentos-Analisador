"""
app.py — Servidor Flask principal do Analisador de Sentimentos

Orquestra o fluxo completo:
1. Permite selecionar a categoria (Play Store, YouTube, Instagram, Amazon)
2. Carrega avaliações simuladas específicas
3. Recupera análises do cache SQLite local (para performance)
4. Envia novos comentários à IA em paralelo
5. Consolida estatísticas e serve para o dashboard
"""

import logging
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv

import cache_service
from data_service import (
    carregar_avaliacoes,
    calcular_estatisticas,
    combinar_avaliacoes_com_analises,
)
from ai_service import analisar_comentarios

# Configuração de logging do servidor Flask
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente do .env
load_dotenv()

# Inicializa o Flask
app = Flask(__name__)

# Inicializa o banco de cache persistente SQLite
cache_service.inicializar_banco()

# Cache em memória por categoria: {'playstore': dados_processados, ...}
_cache_dados: dict[str, dict] = {}


def _processar_dados(categoria: str) -> dict:
    """
    Executa o pipeline completo de processamento para a categoria selecionada:
    JSON específico → Validação → Cache/IA → Estatísticas → Resposta consolidada.
    """
    global _cache_dados

    # Verifica se já está no cache em memória
    if categoria in _cache_dados:
        logger.info(f"Retornando dados do cache em memória para a categoria '{categoria}'")
        return _cache_dados[categoria]

    logger.info(f"Iniciando processamento de dados para a categoria '{categoria}'...")

    # 1. Carregar e validar avaliações
    avaliacoes = carregar_avaliacoes(categoria)
    logger.info(f"Etapa 1: {len(avaliacoes)} avaliações carregadas")

    # 2. Preparar comentários para a IA
    comentarios_para_ia = [
        {"id": a.id, "comentario": a.comentario}
        for a in avaliacoes
    ]

    # 3. Enviar para análise da IA (com cache local e paralelismo)
    try:
        analises, meta_dados = analisar_comentarios(comentarios_para_ia)
        logger.info(f"Etapa 2: {len(analises)} análises recebidas da IA")
    except Exception as e:
        logger.exception("Erro na análise da IA")
        return {
            "erro": str(e),
            "avaliacoes": [],
            "estatisticas": None,
            "performance": {
                "tempo_execucao_ms": 0,
                "total_comentarios": len(comentarios_para_ia),
                "comentarios_do_cache": 0,
                "comentarios_da_ia": len(comentarios_para_ia)
            }
        }

    # 4. Combinar dados originais com análises
    avaliacoes_completas = combinar_avaliacoes_com_analises(avaliacoes, analises)
    logger.info(f"Etapa 3: {len(avaliacoes_completas)} avaliações combinadas")

    # 5. Calcular estatísticas (feito pelo Python, não pela IA)
    estatisticas = calcular_estatisticas(avaliacoes_completas, categoria)
    logger.info("Etapa 4: Estatísticas calculadas")

    # 6. Montar resposta consolidada
    dados = {
        "avaliacoes": [
            {
                "id": a.id,
                "usuario": a.usuario,
                "estrelas": a.estrelas,
                "comentario": a.comentario,
                "data": a.data.isoformat(),
                "analise": a.analise.model_dump(),
                "curtidas": a.curtidas,
                "compartilhamentos": a.compartilhamentos,
                "versao_app": a.versao_app,
                "android_version": a.android_version,
                "duracao_minutos": a.duracao_minutos,
                "categoria_video": a.categoria_video,
                "tipo_midia": a.tipo_midia,
                "hashtag_principal": a.hashtag_principal,
                "dias_entrega": a.dias_entrega,
                "embalagem_status": a.embalagem_status,
            }
            for a in avaliacoes_completas
        ],
        "estatisticas": estatisticas.model_dump(),
        "performance": meta_dados
    }

    # Salva no cache em memória
    _cache_dados[categoria] = dados
    logger.info(f"Processamento concluído para '{categoria}' e salvo no cache em memória")

    return dados


@app.route("/")
def index():
    """Renderiza a página principal do dashboard."""
    return render_template("index.html")


@app.route("/favicon.ico")
def favicon():
    """Retorna o favicon da aplicação."""
    from flask import send_from_directory
    import os
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@app.route("/api/dados/<categoria>")
def api_dados(categoria):
    """
    Retorna todos os dados processados da categoria especificada em JSON.
    """
    from flask import request
    validas = ["playstore", "youtube", "instagram", "amazon"]
    if categoria not in validas:
        return jsonify({"erro": f"Categoria inválida. Opções: {', '.join(validas)}"}), 400

    # Captura campos simulados da interface
    target_id = request.args.get("target_id")
    api_key = request.args.get("api_key")

    if target_id or api_key:
        logger.info("=========================================")
        logger.info(f"[SIMULAÇÃO] Iniciando integração com a API da plataforma '{categoria.upper()}'")
        if target_id:
            logger.info(f"[SIMULAÇÃO] Destino da Extração: {target_id}")
        if api_key:
            masked = api_key[:4] + "********" if len(api_key) > 4 else "********"
            logger.info(f"[SIMULAÇÃO] Token/Chave de API: {masked}")
        logger.info(f"[SIMULAÇÃO] Conexão bem-sucedida! Extraindo dados da plataforma...")
        logger.info(f"[SIMULAÇÃO] Extração completa: 100 avaliações recentes carregadas.")
        logger.info("=========================================")

    try:
        dados = _processar_dados(categoria)
        if "erro" in dados:
            return jsonify(dados), 500
        return jsonify(dados)
    except Exception as e:
        logger.exception(f"Erro ao processar dados para '{categoria}'")
        return jsonify({"erro": str(e)}), 500


@app.route("/api/analisar-avulso", methods=["POST"])
def api_analisar_avulso():
    """
    Recebe um comentário avulso, analisa via IA (com cache persistente) e retorna o resultado.
    """
    from flask import request
    
    data = request.get_json()
    if not data or "texto" not in data:
        return jsonify({"erro": "O campo 'texto' é obrigatório."}), 400
        
    texto = data["texto"].strip()
    if not texto:
        return jsonify({"erro": "O texto não pode ser vazio."}), 400

    comentario_avulso = [{"id": "avulso", "comentario": texto}]

    try:
        analises, _ = analisar_comentarios(comentario_avulso)
        if analises and analises[0]:
            return jsonify(analises[0].model_dump())
        return jsonify({"erro": "Não foi possível obter resposta da IA."}), 500
    except Exception as e:
        logger.exception("Erro ao processar análise avulsa")
        return jsonify({"erro": str(e)}), 500


@app.route("/api/limpar-cache", methods=["POST"])
def limpar_cache():
    """Limpa o cache em memória e o banco de dados SQLite persistente."""
    global _cache_dados
    _cache_dados = {}
    
    try:
        cache_service.limpar_cache_completo()
        logger.info("Todos os caches foram limpos com sucesso")
        return jsonify({"mensagem": "Todos os caches (memória e banco SQLite) foram limpos com sucesso!"})
    except Exception as e:
        logger.exception("Erro ao limpar cache persistente SQLite")
        return jsonify({"erro": f"Cache em memória limpo, mas erro ao limpar SQLite: {e}"}), 500


if __name__ == "__main__":
    logger.info("Iniciando Analisador de Sentimentos...")
    logger.info("Acesse: http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)

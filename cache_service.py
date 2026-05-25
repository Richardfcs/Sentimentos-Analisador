"""
cache_service.py — Serviço de cache persistente local com SQLite

Evita reprocessar comentários já analisados pela IA, economizando
tempo e requisições à API da OpenRouter.
"""

import os
import json
import hashlib
import sqlite3
import logging
from pathlib import Path
from schemas import AnaliseIA

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent / "analises_cache.db"


def inicializar_banco() -> None:
    """Cria o banco de dados SQLite e a tabela de cache caso não existam."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache_comentarios (
                hash_comentario TEXT PRIMARY KEY,
                comentario_original TEXT,
                sentimento TEXT,
                emocao TEXT,
                confianca REAL,
                nivel_criticidade TEXT,
                pontos_positivos TEXT, -- Armazenado como string JSON
                pontos_negativos TEXT, -- Armazenado como string JSON
                resumo TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
        logger.info(f"Banco de dados de cache inicializado com sucesso em {DB_PATH}")
    except Exception as e:
        logger.error(f"Erro ao inicializar o banco de dados de cache: {e}")


def obter_hash_comentario(comentario: str) -> str:
    """Gera um hash SHA256 único a partir do texto do comentário."""
    # Remove espaços extras e normaliza para caixa baixa para evitar duplicatas por formatação
    texto_normalizado = comentario.strip().lower()
    return hashlib.sha256(texto_normalizado.encode("utf-8")).hexdigest()


def buscar_no_cache(comentario: str) -> AnaliseIA | None:
    """
    Busca a análise de um comentário no cache SQLite.

    Args:
        comentario: O comentário textual original.

    Returns:
        Objeto AnaliseIA se encontrado, caso contrário None.
    """
    c_hash = obter_hash_comentario(comentario)
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """SELECT sentimento, emocao, confianca, nivel_criticidade, 
                      pontos_positivos, pontos_negativos, resumo 
               FROM cache_comentarios 
               WHERE hash_comentario = ?""",
            (c_hash,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            sentimento, emocao, confianca, nivel_criticidade, pontos_pos_str, pontos_neg_str, resumo = row
            return AnaliseIA(
                sentimento=sentimento,
                emocao=emocao,
                confianca=confianca,
                nivel_criticidade=nivel_criticidade,
                pontos_positivos=json.loads(pontos_pos_str),
                pontos_negativos=json.loads(pontos_neg_str),
                resumo=resumo
            )
    except Exception as e:
        logger.error(f"Erro ao buscar no cache SQLite: {e}")

    return None


def salvar_no_cache(comentario: str, analise: AnaliseIA) -> None:
    """
    Salva a análise de um comentário no cache SQLite.

    Args:
        comentario: O comentário textual original.
        analise: A análise gerada pela IA.
    """
    c_hash = obter_hash_comentario(comentario)
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO cache_comentarios 
               (hash_comentario, comentario_original, sentimento, emocao, confianca, 
                nivel_criticidade, pontos_positivos, pontos_negativos, resumo) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                c_hash,
                comentario,
                analise.sentimento,
                analise.emocao,
                analise.confianca,
                analise.nivel_criticidade,
                json.dumps(analise.pontos_positivos, ensure_ascii=False),
                json.dumps(analise.pontos_negativos, ensure_ascii=False),
                analise.resumo
            )
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Erro ao salvar no cache SQLite: {e}")


def limpar_cache_completo() -> None:
    """Apaga todos os registros do banco de dados de cache."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cache_comentarios")
        conn.commit()
        conn.close()
        logger.info("Cache persistente SQLite limpo com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao limpar o cache SQLite: {e}")

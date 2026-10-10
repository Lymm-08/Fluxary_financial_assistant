# ==========================
# ARQUIVO: src/models/migrate.py
# SCRIPT DE MIGRAÇÃO DO BANCO DE DADOS
# ==========================

import logging
from sqlalchemy import text, inspect
from datetime import datetime

logger = logging.getLogger(__name__)

def migrate_db(engine):
    """Executa migrações necessárias no banco de dados"""
    
    inspector = inspect(engine)
    
    # Verificar se a tabela 'banks' existe
    if 'banks' not in inspector.get_table_names():
        logger.info("Tabela 'banks' não existe; será criada automaticamente")
        return True
    
    # Obter colunas da tabela 'banks'
    columns = {col['name'] for col in inspector.get_columns('banks')}
    
    # Lista de migrações necessárias
    migrações = [
        {
            'nome': 'Adicionar coluna last_month',
            'coluna': 'last_month',
            'sql': "ALTER TABLE banks ADD COLUMN last_month INTEGER DEFAULT 0",
            'verificar': lambda cols: 'last_month' not in cols
        }
    ]
    
    # Executar migrações
    with engine.connect() as conn:
        for migracao in migrações:
            if migracao['verificar'](columns):
                try:
                    logger.info('Executando migração: %s', migracao['nome'])
                    conn.execute(text(migracao['sql']))
                    conn.commit()
                    logger.info('Migração concluída: %s', migracao['nome'])
                    columns.add(migracao['coluna'])
                except Exception as e:
                    logger.warning('Erro ao executar migração %s: %s', migracao['nome'], e)
                    # Alguns bancos podem dar erro se a coluna já existe
                    if 'already exists' in str(e) or 'duplicate' in str(e).lower():
                        logger.info('Coluna já existe; continuando')
                    else:
                        raise
            else:
                logger.info('Migração já aplicada: %s', migracao['nome'])
    
    logger.info('Migrações concluídas com sucesso')
    return True

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

dotenv_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path)

config = {
    'BOT_TOKEN': os.getenv('BOT_TOKEN', ''),
    'DB_URI': os.getenv(
        'DB_URI',
        'postgresql://localhost:5432/bot_financeiro',
    ),
    'DEBUG': os.getenv('DEBUG', 'False').lower() == 'true',
    'ENCRYPTION_KEY': os.getenv('ENCRYPTION_KEY', ''),
}

if not config['BOT_TOKEN']:
    logger.warning('BOT_TOKEN não configurado no .env')

logger.info('Configuração carregada')
logger.info('BOT_TOKEN: %s', 'configurado' if config['BOT_TOKEN'] else 'NÃO DEFINIDO')
logger.info('DB_URI: %s', 'configurada' if config['DB_URI'] else 'NÃO DEFINIDA')
logger.info('DEBUG: %s', config['DEBUG'])

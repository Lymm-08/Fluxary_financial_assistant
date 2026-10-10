import logging
import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO').upper(),
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)

from src.config.config import config
from src.models.db import init_db
from src.models.migrate import migrate_db


if not config.get('BOT_TOKEN'):
    logger.error('Configure BOT_TOKEN no arquivo .env ou no ambiente.')
    sys.exit(1)

try:
    db_config = init_db(config['DB_URI'])
    logger.info('Banco de dados inicializado com sucesso')
    migrate_db(db_config['engine'])
except Exception as error:
    logger.error('Falha ao inicializar o banco de dados: %s', error)
    sys.exit(1)

try:
    from telegram import Update
    from telegram.error import Conflict
    from telegram.ext import Application

    from src.commands.handlers import register_commands
except ImportError as error:
    logger.error('Dependência ausente: %s', error)
    logger.info('Instale as dependências com: pip install -r requirements.txt')
    sys.exit(1)


def main():
    """Inicializa a aplicação do Telegram e executa o polling."""
    try:
        app = Application.builder().token(config['BOT_TOKEN']).build()
        register_commands(app, db_config)

        logger.info('Bot Financeiro iniciado')
        logger.info('Banco de dados configurado')
        logger.info('Pronto para receber mensagens')
        logger.info('Pressione Ctrl+C para parar')

        for attempt in range(3):
            try:
                app.run_polling(allowed_updates=Update.ALL_TYPES)
                break
            except Conflict as error:
                logger.warning(
                    'Conflito com outra instância do bot (tentativa %d/3): %s',
                    attempt + 1,
                    error,
                )
                if attempt == 2:
                    logger.error(
                        'Não foi possível iniciar o bot. Feche a outra instância '
                        'do bot e tente novamente.'
                    )
                    sys.exit(1)
                logger.info('Tentando novamente em 10 segundos')
                time.sleep(10)
    except KeyboardInterrupt:
        logger.info('Bot parado pelo usuário')
    except Exception as error:
        logger.exception('Falha ao iniciar o bot: %s', error)
        sys.exit(1)


if __name__ == '__main__':
    main()

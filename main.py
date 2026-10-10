import subprocess
import sys
import time
import traceback

from dotenv import load_dotenv

load_dotenv()

from src.config.config import config
from src.models.db import init_db
from src.models.migrate import migrate_db


if not config.get('BOT_TOKEN'):
    print('❌ ERRO: Configure BOT_TOKEN no arquivo .env ou no ambiente.')
    sys.exit(1)

try:
    db_config = init_db(config['DB_URI'])
    print('✅ Banco de dados inicializado com sucesso')
    migrate_db(db_config['engine'])
except Exception as error:
    print(f'❌ ERRO ao inicializar banco: {error}')
    sys.exit(1)

try:
    from telegram import Update
    from telegram.error import Conflict
    from telegram.ext import Application

    from src.commands.handlers import register_commands
except ImportError as error:
    print(f'❌ ERRO: Dependência faltando - {error}')
    print('💡 Execute: pip install -r requirements.txt')
    sys.exit(1)


def kill_existing_python_processes():
    """Tenta encerrar processos Python existentes para evitar conflitos."""
    try:
        result = subprocess.run(
            ['taskkill', '/F', '/IM', 'python.exe', '/T'],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            print('✅ Processos Python existentes foram terminados')
        else:
            print('ℹ️  Nenhum processo Python encontrado ou não foi possível terminar')
    except Exception as error:
        print(f'⚠️  Não foi possível verificar processos Python: {error}')


def main():
    """Inicializa a aplicação do Telegram e executa o polling."""
    try:
        app = Application.builder().token(config['BOT_TOKEN']).build()
        register_commands(app, db_config)

        print('🚀 Bot Financeiro iniciado!')
        print('📊 Banco de dados configurado')
        print('📱 Pronto para receber mensagens...')
        print('(Pressione Ctrl+C para parar)')

        for attempt in range(3):
            try:
                app.run_polling(allowed_updates=Update.ALL_TYPES)
                break
            except Conflict as error:
                print(f'⚠️  Conflito detectado (tentativa {attempt + 1}/3): {error}')
                if attempt == 2:
                    print('❌ Muitas tentativas falharam. Verifique outra instância.')
                    sys.exit(1)
                print('🔄 Aguardando 10 segundos para tentar novamente...')
                time.sleep(10)
                kill_existing_python_processes()
                time.sleep(2)
    except KeyboardInterrupt:
        print('\n⏹️  Bot parado pelo usuário')
    except Exception as error:
        print(f'❌ ERRO ao iniciar bot: {error}')
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

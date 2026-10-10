import os
from pathlib import Path

from dotenv import load_dotenv


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
    print('⚠️  Aviso: BOT_TOKEN não configurado no .env')

print('🔧 Configuração carregada:')
print(f'   - BOT_TOKEN: {"configurado" if config["BOT_TOKEN"] else "NÃO DEFINIDO"}')
print(f'   - DB_URI: {"configurada" if config["DB_URI"] else "NÃO DEFINIDA"}')
print(f'   - DEBUG: {config["DEBUG"]}')

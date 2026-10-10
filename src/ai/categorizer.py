# ==========================
# ARQUIVO: src/ai/categorizer.py
# SISTEMA DE CATEGORIZAÇÃO INTELIGENTE
# ==========================

# ==========================
# IMPORTAÇÕES E CONFIGURAÇÕES
# ==========================

import logging
import os
import time

import requests

logger = logging.getLogger(__name__)

# SUBSEÇÃO: Configuração da API Hugging Face
HF_API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-base"
HF_TOKEN = os.getenv('HF_API_TOKEN', '')

# ==========================
# REGRAS DE FALLBACK
# ==========================

# SUBSEÇÃO: Dicionário de categorias e palavras-chave ( fallback para quando a IA não estiver disponível)
FALLBACK_RULES = {
    'Transporte': ['uber', 'taxi', 'ônibus', 'metrô', 'combustível', 'gasolina', 'passagem', 'trem', 'voo', 'avião', 'estacionamento', 'pedágio', 'transporte'],
    'Alimentação': ['pizza', 'restaurante', 'comida', 'café', 'almoço', 'jantar', 'lanche', 'padaria', 'açaí', 'hamburger', 'sorvete', 'adega', 'mercado', 'feira', 'hortifruti', 'supermercado'],
    'Compras': ['compra', 'market', 'cartao', 'cartão', 'parcela', 'supermercado', 'mercado', 'loja', 'shopping', 'produto', 'roupa', 'sapato', 'eletrônico', 'casa', 'decoração'],
    'Lazer': ['cinema', 'jogo', 'filme', 'diversão', 'show', 'museu', 'teatro', 'viagem', 'hotel', 'parque', 'entretenimento'],
    'Saúde': ['farmácia', 'médico', 'hospital', 'dentista', 'remédio', 'medicamento', 'academia', 'plano de saúde', 'consulta'],
    'Contas': ['conta', 'água', 'luz', 'internet', 'gás', 'telefone', 'energia', 'aluguel', 'condomínio'],
    'Educação': ['curso', 'livro', 'escola', 'aula', 'universidade', 'faculdade', 'material escolar'],
    'Moda': ['roupa', 'sapato', 'blusa', 'calça', 'tênis', 'jaqueta', 'acessório'],
}

# ==========================
# FUNÇÕES DE IA
# ==========================

# ==========================
# CONSULTA À API HUGGING FACE
# ==========================

def query_hf(prompt: str) -> str:
    """Consulta a API do Hugging Face para categorização inteligente"""
    headers = {}
    if HF_TOKEN:
        headers['Authorization'] = f'Bearer {HF_TOKEN}'

    tries = 3
    for attempt in range(tries):
        try:
            resp = requests.post(HF_API_URL, headers=headers, json={"inputs": prompt}, timeout=15)

            if resp.ok:
                data = resp.json()
                # SUBSEÇÃO: Tratamento de diferentes formatos de resposta
                if isinstance(data, dict) and 'error' in data:
                    logger.warning('Tentativa %d: modelo carregando', attempt + 1)
                    time.sleep(2)
                    continue
                if isinstance(data, list) and 'generated_text' in data[0]:
                    return data[0]['generated_text']
                if isinstance(data, str):
                    return data
            else:
                logger.warning(
                    'Tentativa %d: erro na API Hugging Face (HTTP %d)',
                    attempt + 1,
                    resp.status_code,
                )
        except Exception as e:
            logger.warning(
                'Tentativa %d: erro na requisição à API Hugging Face: %s',
                attempt + 1,
                e,
            )
        time.sleep(1)

    logger.warning('IA indisponível; usando categorização por palavras-chave')
    return ''

# ==========================
# FALLBACK POR PALAVRAS-CHAVE
# ==========================

def fallback_categorize(description: str) -> str:
    """Categoriza baseado em palavras-chave quando IA falha"""
    desc_lower = description.lower()
    for category, keywords in FALLBACK_RULES.items():
        for keyword in keywords:
            if keyword in desc_lower:
                return category
    return 'Outros'

# ==========================
# FUNÇÃO PRINCIPAL DE CATEGORIZAÇÃO
# ==========================

def categorize(description: str) -> str:
    """Categoriza uma descrição usando IA + fallback"""
    if not description:
        return 'Outros'

    # SUBSEÇÃO: Prompt para a IA
    prompt = (
        f"Classifique a seguinte descrição de transação financeira em uma única categoria."
        f"\nDescrição: {description}\nCategoria:"
    )

    result = query_hf(prompt)
    if result:
        parts = result.split('Categoria:')
        cat = parts[-1].strip().split('\n')[0].strip()
        if cat and len(cat) > 1:  # evitar caracteres únicos
            return cat

    # SUBSEÇÃO: Usar fallback se IA falhar
    return fallback_categorize(description)

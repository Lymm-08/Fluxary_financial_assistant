# Fluxary — Assistente Financeiro

[English](README.md) | Português (Brasil)

O Fluxary é um bot para Telegram desenvolvido em Python para registrar receitas
e despesas, categorizar transações com a API de inferência da Hugging Face e
consultar resumos financeiros armazenados com SQLAlchemy.

## Funcionalidades

- Registra receitas e despesas a partir de mensagens em texto.
- Categoriza transações com IA da Hugging Face e regras locais de fallback.
- Gera relatórios do mês atual, semanais, mensais e por categoria.
- Persiste transações e saldo em PostgreSQL.

## Tecnologias

Python 3.10+, `python-telegram-bot`, SQLAlchemy, PostgreSQL, API de inferência
da Hugging Face e pytest.

## Estrutura do projeto

| Caminho | Finalidade |
| --- | --- |
| `main.py` | Ponto de entrada da aplicação |
| `src/ai/` | Categorização de transações por IA |
| `src/commands/` | Comandos e handlers do Telegram |
| `src/models/` | Modelos SQLAlchemy e configuração do banco |
| `src/services/` | Geração de relatórios financeiros |
| `src/utils/` | Funções auxiliares de parsing, formatação e criptografia |
| `tests/` | Testes automatizados |

## Instalação e configuração

1. Instale Python 3.10 ou superior e PostgreSQL.
2. Crie e ative um ambiente virtual:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Instale as dependências do projeto:

   ```shell
   python -m pip install -r requirements.txt
   ```

4. Copie `.env.example` para `.env` e configure o token do bot do Telegram,
   a URL de conexão do PostgreSQL e, opcionalmente, o token da Hugging Face.
   Mantenha `.env` privado; esse arquivo não é versionado.
5. Inicie o bot:

   ```shell
   python main.py
   ```

Para iniciar, o bot exige um `BOT_TOKEN` válido e acesso ao banco de dados. Se
o token da Hugging Face não estiver configurado ou a API estiver indisponível,
a categorização utiliza as regras locais por palavras-chave.

## Testes

Instale as dependências de execução e desenvolvimento com
`python -m pip install -r requirements.txt` (pytest já está incluído) e rode:

```shell
python -m pytest
```

A suíte cobre a categorização com chamadas à Hugging Face mockadas (incluindo
timeout e respostas inválidas), interpretação das mensagens, registro de
receitas e despesas em SQLite em memória e cálculos/formatação dos relatórios
semanal, mensal e por categoria. Os testes não exigem credenciais do Telegram
ou da Hugging Face, acesso à rede nem uma instância PostgreSQL.

## Demonstração

![Demonstração do bot Fluxary no Telegram](contacerta.gif)

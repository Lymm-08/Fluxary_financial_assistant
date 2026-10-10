# ==========================
# ARQUIVO: src/commands/handlers.py
# GERENCIAMENTO DE COMANDOS E MENSAGENS DO TELEGRAM
# ==========================

# ==========================
# IMPORTAÇÕES NECESSÁRIAS
# ==========================

import logging
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from functools import partial
from datetime import datetime

from src.ai.categorizer import categorize
from src.utils.formatter import format_money, format_date
from src.utils.parser import parse_transaction_message
from src.services.reports import generate_report, generate_month_specific_report

logger = logging.getLogger(__name__)

# ==========================
# SEÇÃO: COMANDOS PRINCIPAIS
# ==========================

# ==========================
# COMANDO /start e /iniciar
# ==========================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """Comando /iniciar - Menu principal com boas-vindas"""
    user = update.effective_user
    user_id = str(user.id)

    # Verificar se é usuário novo
    session = db['Session']()
    entries_count = session.query(db['Entry']).filter_by(user_id=user_id).count()
    bank = session.query(db['Bank']).filter_by(user_id=user_id).first()
    session.close()

    is_new_user = entries_count == 0 and (not bank or bank.total_balance == 0)

    text = f"""🤖 Bot Financeiro - Olá {user.first_name}!

💰 O que você pode fazer:

• 💸 Registrar despesas/receitas digitando valores
  (ex: 30,9 pizza 🍕 ou 400 salario 💼, 22 recebi pix 💳...)

• 📊 Gerar relatórios: simples e completo
  (comandos: /relatorio simples e /relatorio completo)

• 📅 Relatórios específicos: /relatorio mes (n° do mês)
  (ex: /relatorio mes 8)

• 🔄 Reset mensal automático:
   historico 📚 e saldo 💰 ficam salvos, transações zeram no novo mês

• ⚙️ Comandos:
/reset (zerar tudo 🗑️)
/ajustar_saldo (ajusta o saldo, ex: /ajustar_saldo 200 💵)

----------------------------------------------------------
"""

    keyboard = []
    keyboard.append([InlineKeyboardButton("+ Inserir saldo atual", callback_data='inserir_saldo')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)

# ==========================
# HANDLER DE MENSAGENS LIVRES (REGISTRO DE TRANSAÇÕES)
# ==========================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """Processa mensagens de texto para registrar transações"""
    text = update.message.text
    user_id = str(update.effective_user.id)

    # SUBSEÇÃO: Verificar se está esperando saldo inicial
    if 'waiting_saldo' in context.user_data:
        try:
            valor = float(text.replace(',', '.'))
            session = db['Session']()
            bank = session.query(db['Bank']).filter_by(user_id=user_id).first()
            if not bank:
                bank = db['Bank'](user_id=user_id, total_balance=0, last_month=datetime.now().month)
                session.add(bank)
            bank.total_balance = valor
            session.commit()
            session.close()
            del context.user_data['waiting_saldo']
            await update.message.reply_text(f"✅ Saldo inicial definido: {format_money(valor)}")
            return
        except ValueError:
            await update.message.reply_text("❌ Valor inválido. Digite apenas o número do saldo.")
            return

    # SUBSEÇÃO: Extrair valor e descrição da mensagem
    transaction = parse_transaction_message(text)
    if not transaction:
        await update.message.reply_text("""
❓ Não consegui processar sua mensagem.

📝 Formatos válidos:
• "20 pizza" → R$ 20 em Alimentação
• "pizza 20" → R$ 20 em Alimentação  
• "recebi 1000 salario" → +R$ 1.000 de renda
• "1000" quando solicitado saldo

💡 Digite assim e tente novamente!
""")
        return

    valor, descricao = transaction

    categoria = categorize(descricao)

    # SUBSEÇÃO: Identificar se é receita ou despesa baseado em palavras-chave
    desc_lower = descricao.lower()
    palavras_receita = ['recebi', 'salario', 'bônus', 'ganho', 'renda', 'pagamento', 'depósito', 'bonificação', 'salário', 'prêmio', 'reembolso', 'devolução', 'receita', 'entrada']
    palavras_despesa = ['pago', 'comprei', 'gastei', 'transferência', 'gasto', 'paguei', 'transferi', 'saque', 'débito', 'crédito', 'despesa', 'saída']

    eh_receita = any(p in desc_lower for p in palavras_receita)
    eh_despesa = any(p in desc_lower for p in palavras_despesa)

    # SUBSEÇÃO: Perguntar confirmação se não conseguir identificar
    if not eh_receita and not eh_despesa and categoria == 'Outros':
        mensagem = f"❓ Não consegui identificar se é despesa ou receita.\n\n💰 Valor: R$ {valor:.2f}\n📝 Descrição: {descricao}\n\n📌 Responda com:\n/receita ou /despesa"
        await update.message.reply_text(mensagem)
        context.user_data['pending_transaction'] = {
            'valor': valor,
            'descricao': descricao,
            'categoria': categoria,
            'user_id': user_id
        }
        return

    tipo = 'receita' if eh_receita else 'despesa'

    # SUBSEÇÃO: Verificar mudança de mês (apenas atualizar last_month, manter histórico)
    session = db['Session']()
    current_month = datetime.now().month
    bank = session.query(db['Bank']).filter_by(user_id=user_id).first()
    if bank and bank.last_month != 0 and bank.last_month != current_month:
        # Apenas atualizar o mês, manter transações históricas salvas
        bank.last_month = current_month
        session.commit()

    # SUBSEÇÃO: Salvar transação no banco de dados
    try:
        # Criar entrada
        entry = db['Entry'](
            user_id=user_id,
            type=tipo,
            amount=valor,
            category=categoria,
            description=descricao
        )
        session.add(entry)

        # Atualizar saldo bancario
        if not bank:
            bank = db['Bank'](user_id=user_id, total_balance=0, last_month=current_month)
            session.add(bank)

        if tipo == 'receita':
            bank.total_balance += valor
        else:
            bank.total_balance -= valor

        session.commit()

        # Salvar o saldo ANTES de fechar a sessão
        saldo_atual = bank.total_balance
        session.close()

        resposta = f"""
✅ Registrado com sucesso!

💰 Valor: {format_money(valor)}
📂 Categoria: {categoria}
📝 Descrição: {descricao}
🔄 Tipo: {tipo.capitalize()}
📅 Data: {format_date(datetime.now())}
🏦 Saldo Atual: {format_money(saldo_atual)}
"""
    except Exception as e:
        resposta = f"❌ Erro ao salvar: {str(e)}"

    await update.message.reply_text(resposta)

# ==========================
# SEÇÃO: CONFIRMAÇÃO DE TRANSAÇÕES PENDENTES
# ==========================

# ==========================
# CONFIRMAR TIPO DE TRANSAÇÃO (RECEITA/DESPESA)
# ==========================

async def _confirmar_transacao(tipo, update, context, db):
    """Função genérica para confirmar receita ou despesa

    Args:
        tipo: 'receita' ou 'despesa'
    """
    if 'pending_transaction' not in context.user_data:
        await update.message.reply_text("Nenhuma transação pendente de confirmação.")
        return

    trans = context.user_data.pop('pending_transaction')

    try:
        session = db['Session']()
        entry = db['Entry'](
            user_id=trans['user_id'],
            type=tipo,
            amount=trans['valor'],
            category=trans['categoria'],
            description=trans['descricao']
        )
        session.add(entry)

        bank = session.query(db['Bank']).filter_by(user_id=trans['user_id']).first()
        if not bank:
            bank = db['Bank'](user_id=trans['user_id'], total_balance=0)
            session.add(bank)

        if tipo == 'receita':
            bank.total_balance += trans['valor']
            emoji_sinal = "💚 +"
        else:
            bank.total_balance -= trans['valor']
            emoji_sinal = "❤️ -"

        session.commit()
        saldo = bank.total_balance
        session.close()

        resposta = f"✅ Registrado como {tipo.upper()}!\n\n{emoji_sinal} {format_money(trans['valor'])}\n🏦 Saldo: {format_money(saldo)}"
    except Exception as e:
        resposta = f"❌ Erro: {str(e)}"

    await update.message.reply_text(resposta)


async def cmd_confirma_receita(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """Confirma que a transação pendente é uma receita"""
    await _confirmar_transacao('receita', update, context, db)


async def cmd_confirma_despesa(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """Confirma que a transação pendente é uma despesa"""
    await _confirmar_transacao('despesa', update, context, db)

# ==========================
# SEÇÃO: COMANDOS DE RELATÓRIOS
# ==========================

# ==========================
# COMANDO /relatorio
# ==========================

async def cmd_relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """Gera relatórios financeiros"""
    user_id = str(update.effective_user.id)
    args = context.args

    # Verificar se é relatório de mês específico
    if args and args[0] == 'mes' and len(args) > 1:
        try:
            mes_numero = int(args[1])
            if 1 <= mes_numero <= 12:
                report = generate_month_specific_report(user_id, mes_numero, db)
            else:
                report = "❌ Mês inválido. Use números de 1 a 12."
        except ValueError:
            report = "❌ Mês deve ser um número (1-12)."
    elif not args or args[0] == 'simples':
        report = generate_report(user_id, 'simples', db=db)
    elif args[0] == 'completo':
        report = generate_report(user_id, 'completo', db=db)
    elif args[0] == 'semanal':
        report = generate_report(user_id, 'semanal', db=db)
    elif args[0] == 'mensal':
        report = generate_report(user_id, 'mensal', db=db)
    else:
        report = """
❓ Tipo de relatório inválido.

📊 Tipos disponíveis:
• /relatorio simples - Mês atual
• /relatorio completo - Mês atual detalhado
• /relatorio semanal - Últimos 7 dias
• /relatorio mensal - Últimos 30 dias
• /relatorio mes 1 - Janeiro
• /relatorio mes 2 - Fevereiro
• ... até /relatorio mes 12 - Dezembro
"""

    await update.message.reply_text(report)

# ==========================
# SEÇÃO: COMANDOS ESPECIAIS
# ==========================

# ==========================
# COMANDO /reset
# ==========================

async def _executar_reset(user_id, db):
    """Função auxiliar para executar reset de transações e saldo

    Returns:
        tuple: (sucesso: bool, mensagem: str)
    """
    try:
        session = db['Session']()

        # Apagar todas as transações do usuário
        session.query(db['Entry']).filter_by(user_id=user_id).delete()

        # Resetar saldo bancário
        bank = session.query(db['Bank']).filter_by(user_id=user_id).first()
        if bank:
            bank.total_balance = 0

        session.commit()
        session.close()

        mensagem = "🔄 Reset realizado!\nTodas as transações foram apagadas e o saldo voltou para R$ 0,00."
        return True, mensagem
    except Exception as e:
        mensagem = f"❌ Erro ao resetar: {str(e)}"
        return False, mensagem


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """Reseta todas as transações e saldo do usuário"""
    user_id = str(update.effective_user.id)
    sucesso, resposta = await _executar_reset(user_id, db)
    await update.message.reply_text(resposta)

# ==========================
# COMANDO /ajustar_saldo
# ==========================

async def cmd_ajustar_saldo(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """Ajusta manualmente o saldo do usuário"""
    user_id = str(update.effective_user.id)
    args = context.args

    if not args:
        await update.message.reply_text("⚠️ Use assim: /ajustar_saldo 1000")
        return

    try:
        novo_saldo = float(args[0].replace(',', '.'))
        session = db['Session']()

        bank = session.query(db['Bank']).filter_by(user_id=user_id).first()
        if not bank:
            bank = db['Bank'](user_id=user_id, total_balance=0)
            session.add(bank)

        bank.total_balance = novo_saldo
        session.commit()
        session.close()

        resposta = f"✅ Saldo ajustado!\n🏦 Novo saldo: R$ {novo_saldo:.2f}"
    except Exception as e:
        resposta = f"❌ Erro ao ajustar saldo: {str(e)}"

    await update.message.reply_text(resposta)

# ==========================
# SEÇÃO: CALLBACKS E REGISTRO
# ==========================

# ==========================
# HANDLER DE CALLBACKS (BOTÕES)
# ==========================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """Processa cliques nos botões inline"""
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = str(update.effective_user.id)

    if data == 'reset':
        # SUBSEÇÃO: Executar reset via botão
        sucesso, resposta = await _executar_reset(user_id, db)
        await query.edit_message_text(resposta)

    elif data == 'inserir_saldo':
        # SUBSEÇÃO: Iniciar processo de inserir saldo
        context.user_data['waiting_saldo'] = True
        await query.edit_message_text("Digite o valor do seu saldo inicial (ex: 1000 ou 1000,50):")

# ==========================
# REGISTRO DE COMANDOS
# ==========================

def register_commands(app, db):
    """Registra todos os comandos e handlers no bot"""

    # SUBSEÇÃO: Comandos principais
    app.add_handler(CommandHandler('start', partial(cmd_start, db=db)))
    app.add_handler(CommandHandler('iniciar', partial(cmd_start, db=db)))
    app.add_handler(CommandHandler('relatorio', partial(cmd_relatorio, db=db)))
    app.add_handler(CommandHandler('receita', partial(cmd_confirma_receita, db=db)))
    app.add_handler(CommandHandler('despesa', partial(cmd_confirma_despesa, db=db)))
    app.add_handler(CommandHandler('reset', partial(cmd_reset, db=db)))
    app.add_handler(CommandHandler('ajustar_saldo', partial(cmd_ajustar_saldo, db=db)))

    # SUBSEÇÃO: Callbacks (botões)
    app.add_handler(CallbackQueryHandler(partial(handle_callback, db=db)))

    # SUBSEÇÃO: Handler de mensagens livres
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, partial(handle_message, db=db)))

    logger.info('Comandos registrados com sucesso')

    
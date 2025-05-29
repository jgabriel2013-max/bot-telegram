import os
import json
import asyncio
import nest_asyncio
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Etapas da conversa
avaria, atividade, obra, horas, trabalho, localizacao, apoio, material = range(8)

# ✅ Autenticação com Google Sheets (usando variável de ambiente)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
google_creds = json.loads(os.getenv("GOOGLE_CREDENTIALS"))  # variável de ambiente criada na Render
creds = ServiceAccountCredentials.from_json_keyfile_dict(google_creds, scope)
client = gspread.authorize(creds)
sheet = client.open("bot telegram").sheet1

# Início da conversa
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text("✅ok! responda as perguntas abaixo.\n\nDescrição da avaria:")
    return avaria

async def get_avaria(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["avaria"] = update.message.text
    await update.message.reply_text("Descrição da Tarefa:")
    return atividade

async def get_atividade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["atividade"] = update.message.text
    await update.message.reply_text("Previsão da Mão de obra:")
    return obra

async def get_obra(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["obra"] = update.message.text
    await update.message.reply_text("Previsão horas de trabalho:")
    return horas

async def get_horas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["horas"] = update.message.text
    await update.message.reply_text(
        "Trabalho em:\n- local seguro\n- trabalho em altura\n- trabalho em ar quente\n- espaço confinado"
    )
    return trabalho

async def get_trabalho(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["trabalho"] = update.message.text
    await update.message.reply_text("Localização do trabalho:")
    return localizacao

async def get_localizacao(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["localizacao"] = update.message.text
    await update.message.reply_text("Necessário apoio? (ex: soldador, caldeireiro...)")
    return apoio

async def get_apoio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["apoio"] = update.message.text
    await update.message.reply_text("Necessário material? Se sim, qual e o NI?")
    return material

async def get_material(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["material"] = update.message.text

    # Salvar na planilha
    try:
        sheet.append_row([
            context.user_data["avaria"],
            context.user_data["atividade"],
            context.user_data["obra"],
            context.user_data["horas"],
            context.user_data["trabalho"],
            context.user_data["localizacao"],
            context.user_data["apoio"],
            context.user_data["material"],
        ])
    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao salvar os dados: {e}")
        return ConversationHandler.END

    resumo = (
        f"✅ NOTA SALVA!\n\n"
        f"Avaria: {context.user_data['avaria']}\n\n"
        f"Atividade: {context.user_data['atividade']}\n\n"
        f"Mão de obra: {context.user_data['obra']}\n\n"
        f"Horas: {context.user_data['horas']}\n\n"
        f"Trabalho: {context.user_data['trabalho']}\n\n"
        f"Localização: {context.user_data['localizacao']}\n\n"
        f"Apoio: {context.user_data['apoio']}\n\n"
        f"Material: {context.user_data['material']}"
    )

    await update.message.reply_text(resumo, reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END

# Cancelamento
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Conversa cancelada.\nSe quiser começar de novo, digite 'iniciar nota'.")
    context.user_data.clear()
    return ConversationHandler.END

# Função principal
async def main():
    TOKEN = os.getenv("BOT_TOKEN")  # Corrigido: usar variável de ambiente
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex("(?i)^abrir nota$"), start)],
        states={
            avaria: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_avaria)],
            atividade: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_atividade)],
            obra: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_obra)],
            horas: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_horas)],
            trabalho: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_trabalho)],
            localizacao: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_localizacao)],
            apoio: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_apoio)],
            material: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_material)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.TEXT & filters.Regex("(?i)^cancelar$"), cancel),
        ],
    )

    app.add_handler(conv_handler)
    print("🤖 Bot rodando...")
    await app.run_polling()

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())

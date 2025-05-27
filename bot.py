import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Etapas da conversa
avaria, atividade, obra, horas, trabalho, localização, apoio , material = range(8)

# Autenticação com Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("bot telegram").sheet1

# Início da conversa
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("ok! responda as perguntas abaixo .\n\n  Descreva a avaria :")
    return avaria

async def get_avaria(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["avaria"] = update.message.text
    
    await update.message.reply_text(" Descreva a atividade :")
    return atividade

async def get_atividade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["atividade"] = update.message.text

    await update.message.reply_text("Mão de obra: ")
    return obra

async def get_obra(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["obra"] = update.message.text

    await update.message.reply_text("Quantas horas de trabalho: ")
    return horas

async def get_horas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["horas"] = update.message.text

    await update.message.reply_text("Trabalho em :\nlocal seguro\nTrabalho em altura\nTrabalho em ar quente\nEspaço confinado")
    return trabalho

async def get_trabalho(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["trabalho"] = update.message.text

    await update.message.reply_text("localização do trabalho")
    return localização

async def get_localização(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["localização"] = update.message.text

    await update.message.reply_text("Necessario apoio ? \nex:soldado,caldereiro... ")
    return apoio

async def get_apoio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["apoio"] = update.message.text
    
    await update.message.reply_text("Nessario material ? Se sim qual e o NI ? ")
    return material

async def get_material(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["material"] = update.message.text 


    # Salvar dados na planilha
    sheet.append_row([
        context.user_data["avaria"],
        context.user_data["atividade"],
        context.user_data["obra"],
        context.user_data["horas"],
        context.user_data["trabalho"],
        context.user_data["localização"],
        context.user_data["apoio"],
        context.user_data["material"],
    ])

    # Enviar resumo
    resumo = (
        f"✅ NOTA SALVA!\n\n"
        f" Avaria: {context.user_data['avaria']}\n\n"
        f" Ativiade: {context.user_data['atividade']}\n\n"
        f" Mão de obra: {context.user_data['obra']}\n\n"
        f" Horas: {context.user_data['horas']}\n\n"
        f" Trabalho: {context.user_data['trabalho']}\n\n"
        f" Localização: {context.user_data['localização']}\n\n"
        f" Apoio: {context.user_data['apoio']}\n\n"
        f" Material: {context.user_data['material']}\n"
        
    )
    await update.message.reply_text(resumo)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Nota cancelada.")
    return ConversationHandler.END

async def repetir(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Nota cancelada. Vamos começar de novo.\n\nDescreva a avaria:")
    context.user_data.clear()
    return avaria


# Função principal
async def main():
    app = ApplicationBuilder().token("7738868845:AAEy6OmpYdZ_a-pPmtDBV6RAZ1hFaw5e5tw").build()

    conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT & filters.Regex("^abrir nota$"), start)],
    states={
        avaria: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_avaria)],
        atividade: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_atividade)],
        obra: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_obra)],
        horas: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_horas)],
        trabalho: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_trabalho)],
        localização: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_localização)],
        apoio: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_apoio)],
        material: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_material)],
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
        MessageHandler(filters.TEXT & filters.Regex("^cancelar$"), cancel),
        CommandHandler("repetir", repetir),
        MessageHandler(filters.TEXT & filters.Regex("^repetir$"), repetir),
    ],
)

    app.add_handler(conv_handler)
    print("🤖 Bot rodando...")
    await app.run_polling()

# Executar com suporte para ambientes que já usam asyncio
if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())

#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

import os
import logging
import requests
import configparser

from typing import Dict

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    PicklePersistence,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

ruta = os.path.dirname(__file__)
config = configparser.ConfigParser()
config.read(f'{ruta}/config.ini')

ADMIN = config['BOT_CONFIG']['ADMIN']
SERVER = config['BOT_CONFIG']['SERVER']
TOKEN = config['BOT_CONFIG']['BOTTOKEN']

CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)

reply_keyboard = [
    ["Nombre de jugador", "Usuario de Oculus"],
    ["Id Steam", "Equipo", "Plataforma"],
    ["Hecho"]
]

markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def facts_to_str(user_data: Dict[str, str]) -> str:
    """Helper function for formatting the gathered user info."""
    facts = [f"{key} - {value}" for key, value in user_data.items()]
    return "\n".join(facts).join(["\n", "\n"])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation, display any stored data and ask user for input."""
    reply_text = "Hola, soy el bot del grupo Onward Hispano.\nVamos a recopilar algunos datos para compartir con el grupo."
    if context.user_data:
        reply_text += (
            f"Por ahora, conozco de ti: {', '.join(context.user_data.keys())}."
        )
    else:
        reply_text += (
            "Aún no tengo datos tuyos."
        )
    reply_text += (
            "Puedes añadir datos o modificar los existentes con la opción /registrar_datos. "
    )
    await update.message.reply_text(reply_text)

    return CHOOSING


async def register_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_text = (
        "Pulsa sobre cada botón para introducir el dato correspondiente."
    )
    await update.message.reply_text(reply_text, reply_markup=markup)

    return CHOOSING

async def regular_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the user for info about the selected predefined choice."""
    text = update.message.text.lower()
    context.user_data["choice"] = text
    if context.user_data.get(text):
        reply_text = (
            f"Este es el {text} que me habías indicado: {context.user_data[text]}"
        )
    else:
        reply_text = f"Indícame tu {text}"
    await update.message.reply_text(reply_text)

    return TYPING_REPLY


async def received_information(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store info provided by user and ask for the next category."""
    text = update.message.text
    category = context.user_data["choice"]
    context.user_data[category] = text
    del context.user_data["choice"]

    await update.message.reply_text(
        "Estos son los datos que me has indicado: "
        f"{facts_to_str(context.user_data)}"
        "Puedes rellenar otro dato o modificar alguno.",
        reply_markup=markup,
    )

    return CHOOSING


async def show_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the gathered info."""
    await update.message.reply_text(
        f"Estos son los datos que me has facilitado: {facts_to_str(context.user_data)}"
    )

async def publish_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Saves data in the database"""
    telegram_user = str(update.message.from_user.username)
    key_list = ["usuario de oculus", "id steam", "equipo", "nombre de jugador", "plataforma"]
    data_dict = {"telegram_id":'@'+telegram_user}
    for key in context.user_data.keys():
        if key in key_list:
            data_dict[key] = context.user_data[key]
    
    print(data_dict)
    
    req = requests.post(f'{SERVER}/onward_users/create_user/', json=data_dict, verify=False)
    if int(req.status_code) == 200:
        await update.message.reply_text(
            f"Se han publicado tus datos con el resto del grupo.\nSi deseas borrarlos puedes usar el comando: /borrar_datos"
        )

async def delete_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Deletes data in the database and context"""
    key_list = ["usuario de oculus", "id steam", "equipo", "nombre de jugador", "plataforma"]
    keys_to_delete = []

    for key in context.user_data.keys():
        if key in key_list:
            keys_to_delete.append(key)

    for key in keys_to_delete:
        del context.user_data[key]
    
    telegram_user = str(update.message.from_user.username)
    data_dict = {"telegram_id":'@'+telegram_user}
    req = requests.post(f'{SERVER}/onward_users/delete_user/', json=data_dict, verify=False)
    if int(req.status_code) == 200:
        await update.message.reply_text(
            f"Se han borrado todos tus datos.\nSi quieres volver a registrar datos usa el comando /registrar_datos"
        )
    else:
        await update.message.reply_text(
                f"Ha ocurrido un error. Inténtalo de nuevo más tarde."
            )

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the gathered info and end the conversation."""
    if "choice" in context.user_data:
        del context.user_data["choice"]

    await update.message.reply_text(
        f"""Estos son tus datos registrados: {facts_to_str(context.user_data)}\nSi quieres compartirlos con el grupo, haz clic en el comando /publicar_datos\n
Si quieres corregir alguno, usa el comando /registrar_datos""",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


def main() -> None:
    persistence = PicklePersistence(filepath="conversationbot")
    application = Application.builder().token(TOKEN).persistence(persistence).build()

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("registrar_datos", register_data)],
        states={
            CHOOSING: [
                MessageHandler(
                    filters.Regex("^(Nombre de jugador|Usuario de Oculus|Id Steam|Equipo|Plataforma)$"), regular_choice
                )
            ],
            TYPING_CHOICE: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex("^Hecho$")), regular_choice
                )
            ],
            TYPING_REPLY: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex("^Hecho$")), received_information
                )
            ],
        },
        fallbacks=[MessageHandler(filters.Regex("^Hecho$"), done)],
        name="my_conversation",
        persistent=True,
    )

    application.add_handler(conv_handler)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("mostrar_datos", show_data))
    application.add_handler(CommandHandler("publicar_datos", publish_data))
    application.add_handler(CommandHandler("borrar_datos", delete_data))

    application.run_polling()


if __name__ == "__main__":
    main()

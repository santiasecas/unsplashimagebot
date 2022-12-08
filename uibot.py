# -*- coding: utf-8 -*-
import os
import requests
import configparser

from telegram import ForceReply, Update
from telegram.ext import Updater, CommandHandler, ContextTypes, MessageHandler, Filters

ruta = os.path.dirname(__file__)
config = configparser.ConfigParser()
config.read(f'{ruta}/config.ini')

ADMIN = config['BOT_CONFIG']['ADMIN']


# MANEJADORES DE COMANDOS
def start(update, context):
    nuevo_usuario = str(update.message.from_user.username)
    context.bot.send_message(ADMIN,f'Nuevo usuario: @{nuevo_usuario}')

# Se envía mensaje de ayuda con info
def help(update, context):
    update.message.reply_text('Help!')

# Se envía mensaje de ayuda con info
def ping(update, context):
    update.message.reply_text("pong")

def fetch_picture(update, context):
    msg = update.message.text
    req = requests.head(f'http://api.santibaidez.es:443/unsplash_bot/get_picture/{msg}/')
    print(req)
    update.message.reply_text(req)


# Se inicia el bot
def main():
    TOKEN = config['BOT_CONFIG']['BOTTOKEN']
    
    # Se configura el updater
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Manejadores de comandos
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('ping', ping))
    dp.add_handler(MessageHandler(Filters.text, fetch_picture))
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
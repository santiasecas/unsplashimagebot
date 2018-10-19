# -*- coding: utf-8 -*-
import logging
import os
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

ADMIN = os.environ["ADMIN"]

# MANEJADORES DE COMANDOS
def start(bot, update):
	bot.send_message(ADMIN,'Usuario iniciado: @' + str(update.message.from_user.username))
	update.message.reply_text('Bienvenido ' + update.message.from_user.username)

# Se envía mensaje de ayuda con info
def help(bot, update):
	update.message.reply_text('Help!')

# Se envía mensaje de ayuda con info
def ping(bot, update):
	update.message.reply_text("pong")

def buscarFoto(bot, update):
	update.message.reply_text("https://source.unsplash.com/1000x1000/?" + update.message.text )

def error(bot, update, error):
	logger.warning('Update "%s" caused error "%s"', update, error)

# Se inicia el bot
def startBot():
	TOKEN = os.environ["BOTTOKEN"]
	NAME = "unsplashimagebot"

	# Se usa el puerto de Heroku
	PORT = os.environ.get('PORT')

	# Activa logging
	logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
						level=logging.INFO)
	logger = logging.getLogger(__name__)

	# Se configura el updater
	updater = Updater(TOKEN)
	dp = updater.dispatcher
	
	# Manejadores de comandos
	dp.add_handler(CommandHandler("help", help))
	dp.add_handler(CommandHandler('start', start))
	dp.add_handler(CommandHandler('ping', ping))
	dp.add_handler(MessageHandler(Filters.text, buscarFoto))
	dp.add_error_handler(error)
	
	# Lanza el webhook
	updater.start_webhook(listen="0.0.0.0",
						  port=int(PORT),
						  url_path=TOKEN)
	updater.bot.setWebhook("https://{}.herokuapp.com/{}".format(NAME, TOKEN))
	updater.idle()

if __name__ == "__main__":
startBot()
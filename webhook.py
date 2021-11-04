
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from os import environ
from dotenv import load_dotenv
load_dotenv()
AUTH_TOKEN = environ.get('VIBER_API_KEY')

# сюда нужно вставить инфу со своего бота
viber = Api(BotConfiguration(
    name='PythonSampleBot',
    avatar='',
    auth_token=AUTH_TOKEN
))
viber.set_webhook('https://370d-176-193-71-19.ngrok.io')

print('Done.')
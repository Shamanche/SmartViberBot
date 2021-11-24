
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration

AUTH_TOKEN = '4e059b9c9227e6d1-55eccfee382b0e6f-43c64473e8c9663c'

# сюда нужно вставить инфу со своего бота
viber = Api(BotConfiguration(
    name='PythonSampleBot',
    avatar='',
    auth_token=AUTH_TOKEN
))
viber.set_webhook('https://a004-176-193-71-19.ngrok.io')

print('Done.')
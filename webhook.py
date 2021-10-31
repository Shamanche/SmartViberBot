
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration


# сюда нужно вставить инфу со своего бота
viber = Api(BotConfiguration(
    name='PythonSampleBot',
    avatar='',
    auth_token='4e059b9c9227e6d1-55eccfee382b0e6f-43c64473e8c9663c'
))
viber.set_webhook('https://84a2-89-151-168-111.ngrok.io')

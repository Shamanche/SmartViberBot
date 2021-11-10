BASE_BITRIX_URL = 'https://smartcheb.bitrix24.ru/rest/1/'
URGENT_TASK_TEMPLATE_URL = 'https://smartcheb.bitrix24.ru/company/personal/user/1/tasks/templates/'
URL_TAIL = 'template/edit/'
THREAD_NAME = 'Selenium'
TEMPLATE_LIST = [125, 137]  # шаблоны в которых надо изменить ответственного
#синонимы к именам сотрудников, первым в строке обязательно должно быть "официально имя", как BX24
NAMES = [
    ['александр', 'саша', 'санек', 'санёк', 'сашка', 'саныч'],
    ['владимир', 'володя', 'вова', 'вован', 'вовчик', 'вовик'],
    ['евгений', 'женя', 'женич', 'жека', 'женёк', 'женек'],
    ['антон', 'антошка', 'антоха', 'антуан'],
    ['сергей', 'сережа', 'сега', 'серый', 'серж', 'серега', 'серёга'],
    ['ирина', 'иринка', 'ира', 'ириночка', 'иришка', 'ирочка', 'ириша', 'ирка']
]
# Buildpacks for heroku
# https://github.com/heroku/heroku-buildpack-google-chrome
# https://github.com/heroku/heroku-buildpack-chromedriver
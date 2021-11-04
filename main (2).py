from config import *

import os, time
import bitrix24  # pip install bitrix24-rest
import threading
from threading import Thread
from flask import Flask, request, Response

from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages import VideoMessage
from viberbot.api.messages.text_message import TextMessage

from viberbot.api.viber_requests import ViberConversationStartedRequest
from viberbot.api.viber_requests import ViberFailedRequest
from viberbot.api.viber_requests import ViberMessageRequest
from viberbot.api.viber_requests import ViberSubscribedRequest
from viberbot.api.viber_requests import ViberUnsubscribedRequest

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from dotenv import load_dotenv
load_dotenv()

URL_BITRIX = BASE_BITRIX_URL + os.environ.get('BITRIX_WEBHOOK_KEY') + '/'
BITRIX_LOGIN = os.environ.get('BITRIX_LOGIN')
BITRIX_PASSWORD = os.environ.get('BITRIX_PASSWORD')
VIBER_API_KEY = os.environ.get('VIBER_API_KEY')

SINONIMS = {}
for i in NAMES:
    SINONIMS.update({}.fromkeys(i, i[0].capitalize()))


app = Flask(__name__)


def get_tech_employee_list():
    # получаем список сотрудников тех. отдела
    def in_tech_department(employee):
        # проверка является ли сотрудник сотрдуником тех. отдела
        # отделы из которых выбираем сотрудников
        # 5 - технический отдел
        # 55 - ОСО
        # 53 - ЦТО
        DEPARTMENT_SET = {5, 55, 53}
        if employee['ID'] == '300':  # исключаем "дежурную личность"
            return
        return set(employee['UF_DEPARTMENT']).intersection(DEPARTMENT_SET)

    bx24 = bitrix24.Bitrix24(URL_BITRIX)
    try:
        employee_all = bx24.callMethod(
            'user.get',
            sort='ID',
            order='ASC',
            filter={
                'USER_TYPE': 'employee',
                'ACTIVE': True})
    except bitrix24.BitrixError as err:
        print(err)
        return []
    # отбираем сотрудников технического отдела
    employee_tech = [i for i in employee_all if in_tech_department(i)]
    return employee_tech


def set_tech_employee_list(sender_id):
    # получает в Bitrix24  список сотрудников
    # сохраняет в глобальной переменной
    # отправляет его запросившему
    global tech_employee_list
    tech_employee_list = get_tech_employee_list()
    text = 'Я - робот. А это жалкие людишки:\n' + '\n'.join(
        (i['ID'] + ' ' + i['NAME'] + ' ' + i['LAST_NAME'] for i in tech_employee_list))
    message = TextMessage(text=text)
    viber.send_messages(sender_id, [message])
    return


def waiting(sender_id):
    print('Ожидение...')
    time.sleep(30)
    print('Ожидение завершено')
    text = 'Ответственный назначен.'
    message = TextMessage(text=text)
    viber.send_messages(sender_id, [message])


@app.route('/', methods=['POST'])
def incoming():

    def employee_found_list(employee_list, string_to_find):
        # Возвращает список сотрудников содержащих string_to_find
        # string_to_find может быть имя, фамилия или id
        def is_employee_found(employee, string):
            string = string.strip().lower()
            return (string in (
                employee['NAME'].lower(),
                employee['LAST_NAME'].lower(),
                employee['ID'])
            )
        string_to_find = SINONIMS.get(string_to_find.lower(), string_to_find)
        return [i for i in employee_list if is_employee_found(i, string_to_find)]

    def change_responsible(template_list, employee, sender_id):
        # функция меняет ответственного во всех шаблонах тз списка на заданного сотрудника
        # принимает список шаблонов и сотрудника в формате json
        # возвращает статус 'OK' или текст ошибки
        try:
            id_string = ('https://smartcheb.bitrix24.ru/company/personal/user/'
                         + employee['ID'] + '/')
            if os.name == 'posix':
                chrome_options = webdriver.ChromeOptions()
                chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--no-sandbox")
                driver = webdriver.Chrome(executable_path=os.environ.get(
                    "CHROMEDRIVER_PATH"), chrome_options=chrome_options)
            else:
                browser = webdriver.Chrome('chromedriver.exe')
            browser.get(URGENT_TASK_TEMPLATE_URL)
            # elem = browser.find_element(By.ID, 'login')
            elem = WebDriverWait(browser, 15).until(
                EC.presence_of_element_located((By.ID, "login")))
            elem = elem.send_keys(BITRIX_LOGIN)
            # elem = elem.send_keys('td@21smart.ru')
            # elem = browser.find_element(By.CSS_SELECTOR, 'Button[data-action="submit"]')
            elem = WebDriverWait(browser, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'Button[data-action="submit"]')))
            time.sleep(3)
            elem.click()

            elem = WebDriverWait(browser, 15).until(
                EC.presence_of_element_located((By.ID, "password")))
            elem.send_keys(BITRIX_PASSWORD)
            elem = browser.find_element(
                By.CSS_SELECTOR, 'Button[data-action="submit"]')
            elem.click()

            # ждем пока полностью загрузится таблица
            WebDriverWait(browser, 30).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tr[data-type="task-template"]')))

            for template_number in template_list:
                url_template = URGENT_TASK_TEMPLATE_URL + \
                    URL_TAIL + str(template_number) + '/'
                browser.get(url_template)

                # удаляем текущего ответственного
                responsible = WebDriverWait(browser, 30).until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'div[data-block-name="SE_RESPONSIBLE"]')))
                responsible.find_element(
                    By.CSS_SELECTOR, 'span[title="Отменить выбор"]').click()

                # получаем список сотрудников, которых можно назначить ответственным
                employees = browser.find_element(
                    By.CLASS_NAME, 'ui-selector-popup-container')
                employee_list = employees.find_elements(
                    By.CLASS_NAME, 'ui-selector-item-box')

                # находим заданного сотрудника
                for cur_employee in employee_list:
                    if cur_employee.find_element(By.TAG_NAME, 'a').get_attribute('href') == id_string:
                        cur_employee.click()
                        break

                browser.find_element(
                    By.ID, 'ui-button-panel-save').click()  # сохранить
            text = f"Ответственным назначен: {employee['LAST_NAME']} {employee['NAME']}"
        except Exception as err:
            text = repr(err)
        finally:
            browser.quit()
        message = TextMessage(text=text)
        viber.send_messages(sender_id, [message])
        return

    def answer(viber_message, sender_id):
        incoming_text = viber_message.text.lower().strip(' ?.')
        if len(incoming_text.split()) != 1:
            answer_text = 'Человек, ты используешь слишком много слов. Достаточно одного!'
        elif incoming_text == 'help' or incoming_text == 'хелп':
            answer_text = ('Этот бот разработан для автоматической смены '
                           'ответственного за обработку заявок ЦТО и ОСО. '
                           'Просто напишите в сообщении Имя, Фамилию или id ответственного. '
                           'Список сотрудников берется непосредственно из Bitrix24. '
                           'Для обновления списка сотрудников воспользуйтесь командой "Кто?"')
        elif incoming_text == 'кто':
            # зоздаем поток для запроса в Bitrix24
            thread_bx24 = Thread(
                target=set_tech_employee_list, args=(sender_id,))
            thread_bx24.start()
            answer_text = 'Запрос в Bitrix24 отправлен, подождите.'
        else:
            found_employee_list = employee_found_list(
                tech_employee_list, incoming_text)
            if not found_employee_list:
                answer_text = 'Таких человеков не найдено...'
            elif len(found_employee_list) == 1:
                responsible = found_employee_list[0]
                thread_selenium = Thread(target=waiting, name=THREAD_NAME, args=(sender_id,))
                thread_selenium = Thread(target=change_responsible,
                                         name=THREAD_NAME, args=(TEMPLATE_LIST, responsible, sender_id,))
                if THREAD_NAME in (i.name for i in threading.enumerate()):
                    answer_text = 'Имей терпение, человек! Я уже меняю ответственного. Просто подожди!'
                else:
                    print('Запускаем Selenium')
                    thread_selenium.start()
                    # сделать запуск в виде отдельного потока
                    # status_selenium = change_responsible(TEMPLATE_LIST, responsible)
                    answer_text = 'Назначаю ответственного. Подождите...'
            elif len(found_employee_list) > 1:
                # список сотрудников для отправки
                answer_text = ('Надо выбрать всего одного человека, не двух, не трёх, а всего лишь '
                               'одного. Это же так просто, человек!\n' + '\n'.join(
                                   (i['ID'] + ' ' + i['NAME'] + ' ' + i['LAST_NAME']
                                    for i in found_employee_list)))
            else:
                answer_text = 'Произошло что-то странное...'
        return answer_text

    if not viber.verify_signature(request.get_data(), request.headers.get('X-Viber-Content-Signature')):
        return Response(status=403)

    # this library supplies a simple way to receive a request object
    viber_request = viber.parse_request(request.get_data())

    if isinstance(viber_request, ViberMessageRequest):
        sender_id = viber_request.sender.id
        text = answer(viber_request.message, sender_id)
        message = TextMessage(text=text)
        viber.send_messages(sender_id, [message])
    elif isinstance(viber_request, ViberSubscribedRequest):
        viber.send_messages(viber_request.get_user.id, [
            TextMessage(text="thanks for subscribing!")
        ])
    elif isinstance(viber_request, ViberFailedRequest):
        print('здесь был логгер...')
    return Response(status=200)


if __name__ == "__main__":
    viber = Api(BotConfiguration(
        name='SmartViberBot',
        avatar='',
        auth_token=VIBER_API_KEY
    ))
    tech_employee_list = get_tech_employee_list()  # получаем данные из Bitrix24
    app.run(host='0.0.0.0', port=8080, debug=True, use_reloader=True)

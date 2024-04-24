import telebot
from telebot import types
import os
import httplib2 
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials	
import schedule
import time


bot = telebot.TeleBot('bot_token')

CREDENTIALS_FILE = '321.json'

credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])

httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http = httpAuth)

spreadsheetId = '1ZC9jSeU1wSHD0FiYKIhs7gP5Cgp8yiy0aBDw_3XSo1g'

driveService = apiclient.discovery.build('drive', 'v3', http = httpAuth)
access = driveService.permissions().create(
    fileId = spreadsheetId,
    body = {'type': 'user', 'role': 'writer', 'emailAddress': 'm.utkin.fb@bbooster.io'},
    fields = 'id'
).execute()

spreadsheet = service.spreadsheets().get(spreadsheetId = spreadsheetId).execute()
sheetList = spreadsheet.get('sheets')
for sheet in sheetList:
    print(sheet['properties']['sheetId'], sheet['properties']['title'])
    
sheetId = sheetList[0]['properties']['sheetId']

print('Мы будем использовать лист с Id = ', sheetId)

name = ''
date = ''
dep = ''
prod_1 = ''
prod_2 = ''
zps = ''
zvs = ''
link = ''
week_plan_filename = ''
metric_filename = ''
platform_filename = ''
metric_url = ''
week_plan_url = ''
platform_urls_str = ''
platform_url = []
waiting_users = set()

@bot.message_handler(commands=['start'])

def start(message):
    bot.send_message(message.from_user.id, "Приветствую!")
    if message.text == '/start':
        bot.send_message(message.from_user.id, "Вам будет необходимо ответить на 11 вопросов, что займет примерно 5 минут")
        choise(message)
    else:
        bot.send_message(message.from_user.id, 'Напишите /start, пока что я Вас не понимаю')

def choise(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    item1 = types.KeyboardButton("Начать сейчас!")
    item2 = types.KeyboardButton("Вернуться позже")
    markup.add(item1, item2)
    bot.send_message(message.chat.id, "Выберите один из вариантов:", reply_markup=markup)
    bot.register_next_step_handler(message, on_choise_selected)

def on_choise_selected(message):
    if message.text == "Начать сейчас!":
        bot.send_message(message.chat.id, 'Начнем!')
        bot.send_message(message.chat.id, "Представьтесь, пожалуйста. Напишите своё ФИО")
        bot.register_next_step_handler(message, get_name)
    elif message.text == "Вернуться позже":
        bot.send_message(message.chat.id, 'Буду ждать! На следующий день напомню Вам')
        waiting_users.add(message.chat.id)
        schedule.every().day.do(send_reminder, message.chat.id)
        while message.chat.id in waiting_users:
            schedule.run_pending()
            time.sleep(1)

def send_reminder(chat_id):
    bot.send_message(chat_id, 'Привет! Не забудьте продолжить заполнение формы. Если вы готовы начать, напишите /start.')

def get_name(message):
    global name
    name = message.text
    bot.send_message(message.chat.id, 'Напишите дату заполнения')
    bot.register_next_step_handler(message, get_date)

def get_date(message):
    global date
    date = message.text
    bot.send_message(message.chat.id, 'Какой департамент')
    bot.register_next_step_handler(message, get_department)

def get_department(message):
    global dep
    dep = message.text
    bot.send_message(message.chat.id, 'Спасибо за предоставленную информацию!')
    bot.send_message(message.chat.id, 'Теперь отправьте скриншот плана на неделю')
    bot.register_next_step_handler(message, save_week_plan)

def save_week_plan(message):
    if message.photo:
        global week_plan_filename
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        week_plan_filename = 'week_plan_{}.jpg'.format(message.chat.id)
        with open(week_plan_filename, 'wb') as new_file:
            new_file.write(downloaded_file)
        bot.send_message(message.chat.id, 'Фотография сохранена!')
        bot.send_message(message.chat.id, 'Отправьте скриншот метрик')
        bot.register_next_step_handler(message, save_metric)
    else:
        bot.send_message(message.chat.id, 'Вы не отправили фотографию. Пожалуйста, отправьте скриншот плана на неделю.')
        bot.register_next_step_handler(message, save_week_plan)

def save_metric(message):
    if message.photo:
        global metric_filename
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        metric_filename = 'metric_{}.jpg'.format(message.chat.id)
        with open(metric_filename, 'wb') as new_file:
            new_file.write(downloaded_file)
        bot.send_message(message.chat.id, 'Фотография сохранена!')
        bot.send_message(message.chat.id, 'Напишите продукт своей должности')
        bot.register_next_step_handler(message, get_product_1)
    else:
        bot.send_message(message.chat.id, 'Вы не отправили фотографию. Пожалуйста, отправьте скриншот метрик.')
        bot.register_next_step_handler(message, save_metric)

def get_product_1(message):
    global prod_1
    prod_1 = message.text
    bot.send_message(message.chat.id, 'Напишите продукт своего департамента')
    bot.register_next_step_handler(message, get_product_2)

def get_product_2(message):
    global prod_2
    prod_2 = message.text
    bot.send_message(message.chat.id, 'Какие обязательные Составляющие должны быть в ЗРС')
    bot.register_next_step_handler(message, f_zps)

def f_zps(message):
    global zps
    zps = message.text
    bot.send_message(message.chat.id, 'Какие обязательные Составляющие должны быть в ЗВС')
    bot.register_next_step_handler(message, f_zvs)

def f_zvs(message):
    global zvs
    zvs = message.text
    bot.send_message(message.chat.id, 'Направьте скриншоты задач на платформе написав - "Готово", когда отправите все.')
    bot.register_next_step_handler(message, save_tasks)

def save_tasks(message):
    if message.photo:
        global platform_filename
        global platform_url
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        platform_filename = 'platform_{}.jpg'.format(message.chat.id)
        with open(platform_filename, 'wb') as new_file:
            new_file.write(downloaded_file)
        bot.send_message(message.chat.id, 'Фотография сохранена!')
        platform_url.append(upload_image_to_google_drive(platform_filename))
        bot.register_next_step_handler(message, save_tasks)
    else:
        if message.text == "Готово":
            bot.send_message(message.chat.id, 'Последний вопрос. Если вы ведете проект - ссылка на проект, если нет - отправьте прочерк')
            bot.register_next_step_handler(message, project)
        else:
            bot.send_message(message.chat.id, 'Вы не отправили фотографию. Пожалуйста, отправьте скриншот метрик.')
            bot.register_next_step_handler(message, save_tasks)

def project(message):
    global link
    global platform_urls_str
    link = message.text
    bot.send_message(message.chat.id, 'Благодарю за проходжения мониторинга. Если у нас появятся вопросы, то вам будет назначена координация с менеджером по мониторингу. Хорошего дня')
    week_plan_url = upload_image_to_google_drive(week_plan_filename)
    metric_url = upload_image_to_google_drive(metric_filename)
    platform_urls_str = ','.join(platform_url)
    row = [name, date, dep, week_plan_url, metric_url, prod_1, prod_2, zps, zvs, platform_urls_str, link]
    write_to_google_sheet(row)

    
def write_to_google_sheet(row):
    result = service.spreadsheets().values().append(
        spreadsheetId=spreadsheetId,
          range="Лист номер один!A:D",
        valueInputOption="USER_ENTERED",
        body={"values": [row]}
    ).execute()
    print("Данные успешно записаны в таблицу Google.")

def upload_image_to_google_drive(filename):
    file_metadata = {'name': filename, 'supportsAllDrives': True}
    media = apiclient.http.MediaFileUpload(filename, mimetype='image/jpeg')
    file = driveService.files().create(body=file_metadata, media_body=media, fields='id').execute()
    file_id = file.get('id')
    driveService.permissions().create(
        fileId=file_id,
        body={'type': 'anyone', 'role': 'reader'},
        fields='id'
    ).execute()
    return f'https://drive.google.com/uc?id={file_id}'

bot.polling(none_stop=True, interval=0)

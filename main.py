import telebot
from telebot import types
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import sqlite3
from database.base import *
from pyCryptoPayAPI import pyCryptoPayAPI
import json
import requests
import random
import time
import config as cfg


subscribers = {}

conn = sqlite3.connect('subscription.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        expiration_date TEXT
    )
''')
conn.commit()

crypto = pyCryptoPayAPI(api_token="279955:AAKLMAGCHkua2IKKdl6aLp93yOA8PJkusBk")

bot_token = '7854885401:AAG-uZYw0TpATB2YAYoHib7kaAdbZfy7Dxs'
owner_id = 6844417408
channel_id = '-1002498256555'  # ID вашего канала
channel_username = 'ExcellentSnos'  # Имя вашего канала без "@"
name_bot = 'ExcelentSnosBot'
bot = telebot.TeleBot(bot_token)
admins = [7502169904]
last_raid_time = {}








def load_users():
    try:
        with open('users.txt', 'r') as file:
            return [int(line.strip()) for line in file]
    except FileNotFoundError:
        return []

def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        with open('users.txt', 'w') as file:
            file.write('\n'.join(str(user) for user in users))


def create_users_table(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
    ''')

def update_database():
    with sqlite3.connect('database.db') as connection:
        cursor = connection.cursor()

        # Create the users table if it doesn't exist
        create_users_table(cursor)

        # Проверка на наличие столбца last_interaction
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        if "last_interaction" not in columns:
            cursor.execute('''
                ALTER TABLE users ADD COLUMN last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
            ''')
            connection.commit()

update_database()


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if message.text == '/start':
        save_user(user_id)
    user_id = message.from_user.id
    is_subscribed = False
    # Проверяем наличие активной подписки у пользователя
    with sqlite3.connect('subscriptions.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT expiration_date FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()

    if result:
        expiration_date = datetime.strptime(result[0], "%Y-%m-%d").date()
        if expiration_date >= datetime.now().date():
            is_subscribed = True

    if is_subscribed:

        photo_path = 'net.jpg'  # Путь к вашей фотографии для подписанных пользователей
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)

        btn_report = telebot.types.InlineKeyboardButton(callback_data='report', text='🚨 Репортер')
        btn_account = telebot.types.InlineKeyboardButton(callback_data='account', text='💻 Профиль')
        btn_info = telebot.types.InlineKeyboardButton(callback_data='info', text='ℹ️ Информация')

        markup.add(btn_report)
        markup.row(btn_account, btn_info)

        with open(photo_path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo,
                           caption='''`Добро пожаловать в бота для сноса Каналов, Ботов, Чатов, ебни своего обидчика!`''',
                           reply_markup=markup, parse_mode="Markdown")
    else:
        # Если подписки у пользователя нет, создаем счет для оплаты подписки
        invoice = crypto.create_invoice(asset='USDT', amount=4.3)
        pay_url = invoice['pay_url']
        invoice_id = invoice['invoice_id']
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("Купить Подписку (4.3$)", url=pay_url))
        keyboard.add(types.InlineKeyboardButton("Проверить оплату", callback_data=f"check_status_{invoice_id}"))

        photo_path = 'net1.png'  # Путь к вашей фотографии
        with open(photo_path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo,
                           caption=f"Привествую!\nExcelentSnos сносер бот нового поколения! отлетит абсолютно любой!nПЕРЕД ИСПОЛЬЗОВНИЕМ НАЖМИ ИНФОРМАЦИЯ!",
                           reply_markup=keyboard),


@bot.callback_query_handler(func=lambda c: c.data.startswith('check_status'))
def check_status(callback_query):
    invoice_id = callback_query.data.split('_')[2]
    old_invoice = crypto.get_invoices(invoice_ids=invoice_id)
    status_old_invoice = old_invoice['items'][0]['status']
    user_id = callback_query.from_user.id

    if status_old_invoice == "paid":
        bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        bot.send_message(user_id, f"Спасибо за оплату!")

        # Добавляем пользователя в базу данных как подписчика
        with sqlite3.connect('subscriptions.db') as conn:
            cursor = conn.cursor()
            expiration_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")  # Предположим, что подписка действует 30 дней
            cursor.execute('INSERT OR REPLACE INTO users (user_id, expiration_date) VALUES (?, ?)', (user_id, expiration_date))
            conn.commit()

        # Отправляем сообщение пользователю о том, что подписка активирована
        bot.send_message(user_id, "Подписка успешно активирована!")
    elif status_old_invoice == "active":
        bot.send_message(user_id, f"Вы не оплатили счет!")
    else:
        bot.send_message(user_id, f"Счет {invoice_id} не найден.")




@bot.callback_query_handler(func=lambda call: call.data == "info")
def info(call):
    message_text = "*ExcellentSnos* - `это УНИКАЛЬНЫЙ бот в телеграм через которого вы можете сносить каналы ваших обидчиков!`"
    # Создаем клавиатуру с кнопками
    keyboard = types.InlineKeyboardMarkup()
    btn_channel = types.InlineKeyboardButton(callback_data='channel', text='🔋 Канал')
    btn_support = types.InlineKeyboardButton(callback_data='support', text='🆘 Информация')
    btn_back = types.InlineKeyboardButton(callback_data='back', text='↖️ Назад')

    keyboard.row(btn_channel, btn_support)
    keyboard.row(btn_back)

    bot.send_message(call.message.chat.id, message_text, reply_markup=keyboard, parse_mode="Markdown")


    @bot.callback_query_handler(func=lambda call: call.data == "channel")
    def channel(call):
        markup = telebot.types.InlineKeyboardMarkup()
        btn_subscribe = telebot.types.InlineKeyboardButton(text='🌐 Канал с Новостями', url='https://t.me/ExcellentSnos')
        markup.add(btn_subscribe)
        bot.send_message(call.message.chat.id, 'Наш канал:', reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data == "support")
    def support(call):
        markup = telebot.types.InlineKeyboardMarkup()
        btn_subscribe = telebot.types.InlineKeyboardButton(text='⚠️Информация', url='https://t.me/ExcellentSnosInfo')
        markup.add(btn_subscribe)
        bot.send_message(call.message.chat.id, 'Наша поддержка:', reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data == "back")
    def back(call):
        # Создаем клавиатуру с нужными кнопками
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        btn_report = telebot.types.InlineKeyboardButton(callback_data='report', text='🚨 Снос')
        btn_account = telebot.types.InlineKeyboardButton(callback_data='account', text='💻 Профиль')
        btn_info = telebot.types.InlineKeyboardButton(callback_data='info', text='ℹ️ Информация')
        markup.add(btn_report, btn_account, btn_info)

        # Отправляем сообщение с фото и клавиатурой
        photo_path = 'net.jpg'  # Путь к вашей фотографии
        with open(photo_path, 'rb') as photo:
            bot.send_photo(call.message.chat.id, photo, caption="Выберите действие:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "account")
def account(call):
    user_id = call.from_user.id
    user_first_name = call.from_user.first_name
    user_last_name = call.from_user.last_name
    user_username = call.from_user.username

    with sqlite3.connect('subscriptions.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT expiration_date FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()

    if result:
        expiration_date = datetime.strptime(result[0], "%Y-%m-%d").date()
        days_left = (expiration_date - datetime.now().date()).days

        message = f'''💻 Профиль:

📇 Данные: `{user_id} | @{user_username}`
⏳Осталось дней подписки: `{days_left}`

🕰 Подписка до: `{expiration_date}`
'''

        bot.send_message(call.message.chat.id, message, parse_mode="Markdown")  # Добавлен параметр parse_mode="Markdown"
    else:
        bot.send_message(call.message.chat.id, "Извините, но у вас нет активной подписки.")



def update_subscription(user_id, days):
    current_date = datetime.now().date()
    new_expiration_date = current_date + timedelta(days=days)

    with sqlite3.connect('subscriptions.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, expiration_date) VALUES (?, ?)
            ''', (user_id, new_expiration_date.strftime('%Y-%m-%d')))

@bot.message_handler(commands=['admin'])
def admin_command(message):
    user_id = message.from_user.id
    if user_id in admins:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(types.InlineKeyboardButton('Рассылка', callback_data='mailing'))
        bot.send_message(user_id, f"☀️ <b>Добро пожаловать в админ панель!</b>\n\n👤 Всего пользователей: <code>{len(load_users())}</code>", parse_mode='HTML', reply_markup=keyboard)
    else:
        bot.send_message(user_id, "❌ Вы не администратор!")

@bot.callback_query_handler(func=lambda call: call.data == 'mailing' and call.from_user.id in admins)
def mailing_callback(call):
    user_id = call.from_user.id
    bot.send_message(user_id, "📣 | Введите сообщение для рассылки")
    bot.register_next_step_handler(call.message, mailing_process)

def mailing_process(message):
    text = message.text
    users = load_users()
    sent_count = 0
    for user_id in users:
        try:
            bot.send_message(user_id, text)
            sent_count += 1
        except:
            pass
    bot.send_message(message.from_user.id, f"📣 | <b>Рассылка завершена!</b>\n\nМы смогли отправить сообщение {sent_count}/{len(users)} пользователям!", parse_mode='HTML')


@bot.message_handler(commands=['givesub'])
def grant_subscription(message):
    if message.from_user.id == owner_id:
        try:
            command_parts = message.text.split()
            if len(command_parts) == 3:
                user_id = int(command_parts[1])
                days = int(command_parts[2])

                update_subscription(user_id, days)
                bot.reply_to(message, f"Пользователю с ID {user_id} предоставлена подписка на {days} дней!")
                bot.send_message(user_id, f" ✅ | Вам выдали подписку {days} Дней!")

            else:
                bot.reply_to(message, "Неправильный формат команды. Используйте /givesub user_id days")
        except Exception as e:
            bot.reply_to(message, f"Произошла ошибка: {e}")
    else:
        bot.reply_to(message, "У вас нет разрешения для выполнения этой команды!")


@bot.message_handler(commands=['demote'])
def demote_user(message):
    try:
        user_id_to_demote = int(message.text.split()[1])
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "Неверный Айди")
        return

    # Assuming you have defined bot and imported sqlite3 properly

    with sqlite3.connect('subscriptions.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id_to_demote,))
        conn.commit()

    bot.send_message(message.chat.id,
                     f"Подписка у {user_id_to_demote} забрана ")

    # Send message to the user whose subscription has been revoked
    bot.send_message(user_id_to_demote,
                     f" ❌ | У вас Забрали Подписку!\nЕсли не согласны с решением, отпишите: @mirai_mudro")


@bot.message_handler(commands=['bot'])
def help(message):
    bot.send_message(message.chat.id, "Флудить через команду /raid\nПример\n/raid ПР ПР ПР")
    if message.chat.id == cfg.admin or cfg.admin2:
        bot.send_message(message.chat.id,
                         "Напиши /raid в группе и я начну рейд сообщениями. Чтобы добавить меня в группу вам нужно быть админом либо попросить админа добавить вашего бота в группу")
        bot.reply_to(message, "Удачного вам рейда! 😁")



@bot.message_handler(func=lambda message: message.text.startswith('/raid'))
def process_raid(message):
    raid_text = message.text[6:]  # Получаем текст для рейда, исключая "/raid " из начала сообщения
    for i in range(100):  # Отправляем сообщения 10 раз для демонстрационных целей
        bot.send_message(message.chat.id, raid_text)

@bot.message_handler(commands=['stopraid'])
def stop_raid(message):
    if message.chat.id in last_raid_time:
        del last_raid_time[message.chat.id]  # Удаляем время последнего использования команды /raid
        bot.send_message(message.chat.id, "Рейд остановлен.")


# Adding the main logic for sending reports
# Adding the main logic for sending reports
@bot.callback_query_handler(func=lambda call: call.data == "report")
def report(call):
    markup = telebot.types.InlineKeyboardMarkup()
    for i, subject in enumerate(subjects):
        btn_report_type = telebot.types.InlineKeyboardButton(callback_data=f'report_type_{i}', text=subject)
        markup.add(btn_report_type)

    bot.send_message(call.message.chat.id, "Выберите тип жалобы:", reply_markup=markup)

sent_messages = 0
failed_messages = 0

@bot.callback_query_handler(func=lambda call: call.data.startswith("report_type"))
def report_type_selected(call):
    try:
        report_type_index = int(call.data.split("_")[2])
        report_type = subjects[report_type_index]
        bot.send_message(call.message.chat.id, f"Вы выбрали тип жалобы: {report_type}")
        bot.send_message(call.message.chat.id, "Теперь отправьте ссылку на нарушающий канал:\nЕсли вы не отправите ссыку на канал в формате https://t.me/ \n То бот не отправит сообщения на почту")

        subscribers[call.message.chat.id] = {"report_type": report_type}
        bot.register_next_step_handler(call.message, handle_report_link)



    except (IndexError, ValueError) as e:
        bot.send_message(call.message.chat.id, "Произошла ошибка. Пожалуйста, выберите тип жалобы снова.")



def handle_report_link(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    link = message.text
    report_type = subscribers[chat_id]["report_type"]


def handle_report_link(message):
    global sent_messages, failed_messages  # Объявляем глобальные переменные
    chat_id = message.chat.id
    user_id = message.from_user.id
    link = message.text
    report_type = subscribers[chat_id]["report_type"]

    if report_type == 'ДЕАНОН':
        text = f" Здравствуйте, уважаемая поддержка Telegram. Я бы хотел вам сообщить о\nканале, нарушающем правила площадки.\n{link}\nНарушения:\nЛичная информация. В канале сливаются базы данных с личной информацией\nо пользователях/деаноны.Ниже прикрепляю доказательства:\nНиже прикрепляю доказательства: Ссылка на посты/пост"
    elif report_type == 'СВАТИНГ':
        text = f"Здравствуйте, уважаемая поддержка Telegram. Я бы хотел вам сообщить о\nканале, нарушающем правила площадки.\n{link}\nНарушения:\nДанные администраторы канала занимаются Сватингом людей в Интернете\nо пользователях/деаноны.Ниже прикрепляю доказательства:\nНиже прикрепляю доказательства: Ссылка на посты/пост"
    elif report_type == 'РАСПРАВЫ':
        text = f"Здравствуйте, уважаемая поддержка Telegram. Я бы хотел вам сообщить о\nканале, нарушающем правила площадки.\n{link}\nНарушения:\nРасправы\nНиже прикрепляю доказательства: Ссылка на посты/пост"
    elif report_type == 'ПОРНО':
        text = f"Здравствуйте, уважаемая поддержка Telegram. Я бы хотел вам сообщить о\nканале, нарушающем правила площадки.\n{link}\nНарушения:\nПорнография\nНиже прикрепляю доказательства: Ссылка на посты/пост"
    elif report_type == 'НАКРУТКА':
        text = f"Здравствуйте, уважаемая поддержка Telegram. Я бы хотел вам сообщить о\nканале, нарушающем правила площадки.\n{link}\nНарушения:\nВладелец канала сделал себе не настоящих подписчиков, что называется накруткой людей\nНиже прикрепляю доказательства: Ссылка на посты/пост"
    elif report_type == 'СНОС ПРАЙСА':
        text = f"Здравствуйте, уважаемая поддержка Telegram. Я бы хотел вам сообщить о\nканале, нарушающем правила площадки.\n{link}\nНарушения:\nДанный человек продает в своем канале незаконные услуги, а именно:\nДеонимизация личности\nСватинг личности\nПродажа мануалов по Деонимизации, Сватингу\nНиже прикрепляю доказательства: Ссылка на посты/пост\nПрошу заблокировать данный Телеграм Канал"
    elif report_type == 'НАРК0ТИКИ':
        text = f'Здравствуйте, уважаемая поддержка Telegram. Я бы хотел вам сообщить о\nканале, нарушающем правила площадки.\n{link}\nНарушения:\nДанный канал продает в наркотические вещества\nПрошу заблокировать данный Телеграм Канал'
    elif report_type == 'СНОС АКАУНТА ЗА ВИРТ НОМЕР':
        text = f'Здравствуйте, уважаемая поддержка Telegram. Я бы хотел вам сообщить о\nакаунте, нарушающем правила площадки.\n{link}\nНарушения:\nДанный акаунт сидит не с основного номера телефона\nА с Виртуального, как говорит он сам\nПрошу заблокировать данный Телеграм Акаунт'
    elif report_type == 'СНОС АКАУНТА ЗА ДЕАНОН/СВАТ':
        text = f'Здравствуйте, данный телеграмм аккаунт: {link}\nПродает услуги деанонизации личности и сваттинг'
    else:
        text = f"Здравствуйте, уважаемая поддержка Telegram. Я бы хотел вам сообщить о\nканале, нарушающем правила площадки.\n{link}\nНарушения: Неизвестный тип жалобы\nНиже прикрепляю доказательства: Ссылка на посты/пост"



    senderemail, senderpassword = senders[0]
    subject = report_type
    recipient = "Abuse@telegram.org, spam@telegram.org, security@telegram.org, legal@telegram.org, support@telegram.org,sticker@telegram.org, stopCA@telegram.org, recover@telegram.org, DMCA@telegram.org"

    for sender_email, sender_password in senders:
        try:
            sendemail(senderemail, senderpassword, recipient, subject, text)
            sent_messages += 1
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")
            failed_messages += 1

    bot.send_message(chat_id, f"✅Все письма были успешно отправлены✅\n"
                              f"❌Не отправлено сообщений❌: {failed_messages}")


def sendemail(senderemail, senderpassword, recipient, subject, messagetext):
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(senderemail, senderpassword)

        message = MIMEMultipart()
        message['From'] = senderemail
        message['To'] = recipient
        message['Subject'] = subject

        body = messagetext
        message.attach(MIMEText(body, 'plain'))

        server.send_message(message)
        now = datetime.now()
        print(now.strftime("%H:%M:%S"))
        print(f"Письмо от {senderemail} успешно отправлено на {recipient}.")
        server.quit()
    except Exception as e:
        print(f"Письмо не отправлено по причине: {e}")




senders = [
    ('deanonsword@gmail.com', 'mbugrov2006'),
	('avagicog66@gmail.com', 'owqu idec uewp rfar'),
	('enohegiti06@gmail.com', 'chij bdjt qpbc gslh'),
	('oxalewajopuv10@gmail.com', 'lrky cwmk ldfe zxzw'),
	('ebaxowofex65@gmail.com', 'ldwc sjte vuro oexf'),
	('osutokudu06@gmail.com', 'gscs ztmn suqx nnsb'),
    ('mifekafiza34@gmail.com', 'fita bzzs ujcc zcik'),
	('kawubadixen23@gmail.com', 'hwfl jsee jiuk wkab'),
	('ezezeludaz27@gmail.com', 'ofxg arpz brcd pyip'),
	('ziduqujukihu51@gmail.com', 'asza eial mrkc xdbh'),
    ('pagodegey076@gmail.com', 'vgkv ullp djyw fxil')
]
subjects = [
    'ДЕАНОН',
    'СВАТИНГ',
    'РАСПРАВЫ',
    'ПОРНО',
    'НАКРУТКА',
    'СНОС ПРАЙСА',
    'НАРК0ТИКИ',
    'СНОС АКАУНТА ЗА ВИРТ НОМЕР',
    'СНОС АКАУНТА ЗА ДЕАНОН/СВАТ'
]

if __name__ == '__main__':
    # Создание и настройка подключения к базе данных
    db_connect = UserDatabase('database/users.db')
    db_connect.connect()
    db_connect.create_table_user()

    # Запуск бота на постоянном опросе
    bot.polling(none_stop=True)
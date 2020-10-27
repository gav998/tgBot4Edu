from settings import TOKEN
from utils import *

import time
import telebot

bot = telebot.TeleBot(TOKEN)

users = {}

# ожидание команды start
@bot.message_handler(commands=['start'])
def f1_1(message):
    try:
        print(message.from_user.id, message.text, "f1_1")
        if message.content_type != "text":
            raise Exception("Ожидалось текстовое сообщение")

        # если пользователь авторизован
        login = get_login_authorization(message.from_user.id)
        if login is not None:
            msg = bot.send_message(message.chat.id, f'Вы уже авторизованы под логином {login}')
            f2_1(message)
            #- деавторизуем, но надо другой командой. не тут
        else:
            # просим указать номер по списку в ЭЖД
            msg = bot.send_message(message.chat.id,
                                   f'Привет, {message.from_user.first_name}!\n\n' +
                                   f'Я бот проекта школы №1191! Для авторизации укажи свой идентификационный код:\n' +
                                   f'(номер класса)(буква класса)_(номер по списку в ЭЖД)\n\n' +
                                   f'Например, для ученика 7Б класса под номером 11 в ЭЖД, идентификационный код будет таким: 7Б_11\n')
            # ожидаем номера ЭЖД
            bot.register_next_step_handler(msg, f1_2)

    except Exception as e:
        print(e)
        msg = bot.send_message(message.chat.id, 'oooops, попробуйте еще раз..')
        bot.register_next_step_handler(msg, f1_1)


# ожидаем номер ЭЖД
def f1_2(message):
    try:
        print(message.from_user.id, message.text, "f1_2")
        if message.content_type != "text":
            raise Exception("Ожидалось текстовое сообщение")

        # если такой пользователь существует, то и пароль у него существует
        password = get_password(message.text)
        if password is not None:
            msg = bot.send_message(message.chat.id,
                                   "Такой пользователь уже зарегистрирован!\n\nВведите, пожалуйста, пароль:\n")
            # ожидаем пароль пользователя
            users[message.from_user.id] = message.text
            bot.register_next_step_handler(msg, f1_3)
        # иначе
        else:
            # генерируем пароль новому пользователю
            password = random_pass()
            # сохраняем его пароль
            create_user(message.text, password)
            # сообщаем пользователю его пароль
            msg = bot.send_message(message.chat.id, f'Тебе назначен пароль:\n')
            msg = bot.send_message(message.chat.id, password)
            # авторизуем пользователя
            set_login_authorization(message.text, message.from_user.id)
            # отправляем его в функцию выбора предмета
            f2_1(message)

    except Exception as e:
        print(e)
        msg = bot.send_message(message.chat.id, 'oooops, попробуйте еще раз..')
        bot.register_next_step_handler(msg, f1_2)


# ожидаем пароль
def f1_3(message):
    try:
        print(message.from_user.id, message.text, "f1_3")
        if message.content_type != "text":
            raise Exception("Ожидалось текстовое сообщение")

        # сверка паролей    
        password = get_password(users[message.from_user.id])
        if message.text == password:
            #- тут надо деавторизовать предыдущего tg_user_id если такой есть, и написать ему сообщение, что он того.. 
            # авторизуем пользователя
            set_login_authorization(users[message.from_user.id], message.from_user.id)
            msg = bot.send_message(message.chat.id, f'Успешно')
            # отправляем его в функцию выбора предмета
            f2_1(message)
        else:
            raise Exception("Пароль не совпал")

    except Exception as e:
        print(e)
        msg = bot.send_message(message.chat.id, 'oooops, попробуйте еще раз..')
        msg = bot.send_message(message.chat.id, 'Введите идентификационный код')
        bot.register_next_step_handler(msg, f1_2)


# выбор предмета
def f2_1(message):
    try:
        print(message.from_user.id, message.text, "f2_1")
        msg = bot.send_message(message.chat.id, f'Доступен выбор предмета:\n')
        
    except Exception as e:
        print(e)
        msg = bot.send_message(message.chat.id, 'oooops, попробуйте еще раз..')
        bot.register_next_step_handler(msg, f2_1)

if __name__ == "__main__":
    start = time.time()
    print('start bot')
    bot.polling()
    print(time.time() - start)

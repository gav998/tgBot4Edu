from settings import TOKEN
from utils import *

import time
import telebot

bot = telebot.TeleBot(TOKEN)

users = {}
# users[tg_id]['login']
# users[tg_id]['subject_num']
# users[tg_id]['subject_path']
# users[tg_id]['subject']
# users[tg_id]['topic_num']
# users[tg_id]['topic']
# users[tg_id]['task']['task_id']
# users[tg_id]['task']['difficulty_level']
# users[tg_id]['task']['text']
# users[tg_id]['task']['attachment']
# users[tg_id]['task']['correct_answer']

subjects = get_subjects()
# subjects[№]['topics'][№]['name']
# subjects[№]['topics'][№]['levels'][№]


# ожидание команды start
@bot.message_handler(commands=['start'])
def f1_1(message):
    try:
        print(message.from_user.id, message.text, "f1_1")
        if message.content_type != "text":
            raise Exception("Ожидалось текстовое сообщение")

        users[message.from_user.id] = {}
        # если пользователь авторизован
        login = get_login_authorization(message.from_user.id)
        if login is not None:
            msg = bot.send_message(message.chat.id, f'Вы уже авторизованы под логином {login}')
            users[message.from_user.id]['login'] = login
            f2_1(message)
        else:
            # просим указать номер по списку в ЭЖД
            s = f'Здравствуйте, {message.from_user.first_name}!\n\n'
            s += f'Данный телеграмм чат создан командой школы 1191 для тестирования обучающихся.\n'
            s += f'Это opensource проект (https://github.com/gav998/tgBot4Edu/).\n'
            s += f'Ты можешь поучаствовать в его доработке,'
            s += f'присоединяйся к сообществу.\n\n'
            s += f'Для старта тренировок укажи свой идентификационный код:\n'
            s += f'(номер класса)(буква класса)_(номер по списку в ЭЖД)\n\n'
            s += f'Например, для ученика 7Б класса под номером 11 в ЭЖД,'
            s += f'идентификационный код будет таким: 7Б_11\n'
            msg = bot.send_message(message.chat.id, s)

            # ожидаем номера ЭЖД
            bot.register_next_step_handler(msg, f1_2)

    except Exception as e:
        print(e)
        msg = bot.send_message(message.chat.id,
                               f'{e}\noooops, попробуйте еще раз..\n\nВведите /start для продолжения')


# ожидаем номер ЭЖД
def f1_2(message):
    try:
        print(message.from_user.id, message.text, "f1_2")
        if message.content_type != "text":
            raise Exception("Ожидалось текстовое сообщение")
        if not check_re(message.text):
            raise Exception("Неправильный формат идентификационного кода")
        users[message.from_user.id]['login'] = message.text

        # если такой пользователь существует, то и пароль у него существует
        password = get_password(message.text)
        if password is not None:
            msg = bot.send_message(message.chat.id,
                                   f"Такой пользователь уже зарегистрирован!\n\nВведите, пожалуйста, пароль:\n")
            # ожидаем пароль пользователя
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
        msg = bot.send_message(message.chat.id,
                               f'{e}\noooops, попробуйте еще раз..\n\nВведите /start для продолжения')


# ожидаем пароль
def f1_3(message):
    try:
        print(message.from_user.id, message.text, "f1_3")
        if message.content_type != "text":
            raise Exception("Ожидалось текстовое сообщение")

        # сверка паролей    
        password = get_password(users[message.from_user.id]['login'])
        if message.text == password:
            # - тут надо деавторизовать предыдущего tg_user_id если такой есть, и написать ему сообщение, что он того..
            # авторизуем пользователя
            set_login_authorization(users[message.from_user.id]['login'], message.from_user.id)
            # - при попытке авторизовать др tg_id возникнет исключение бд т.к. записи уникальны должны быть
            msg = bot.send_message(message.chat.id, f'Успешно')
            # отправляем его в функцию выбора предмета
            f2_1(message)
        else:
            raise Exception("Пароль не совпал")

    except Exception as e:
        print(e)
        msg = bot.send_message(message.chat.id,
                               f'{e}\noooops, попробуйте еще раз..\n\nВведите /start для продолжения')


# выбор предмета
def f2_1(message):
    try:
        print(message.from_user.id, message.text, "f2_1")

        s = "Доступен выбор предмета. Укажите только номер:\n"
        for i in range(0, len(subjects)):
            s += f"{i + 1}. {subjects[i]['name']}\n"

        msg = bot.send_message(message.chat.id, s)
        bot.register_next_step_handler(msg, f2_2)

    except Exception as e:
        print(e)
        msg = bot.send_message(message.chat.id,
                               f'{e}\noooops, попробуйте еще раз..\n\nВведите /start для продолжения')


# ожидаем выбор предмета и запрашиваем тему
def f2_2(message):
    try:
        print(message.from_user.id, message.text, "f2_2")
        if message.content_type != "text":
            raise Exception("Ожидалось текстовое сообщение")
        if not message.text.isnumeric():
            raise Exception("Ожидалось число")
        if int(message.text) > len(subjects):
            raise Exception("Такого предмета нет в списке")

        # запоминаем номер предмета, который выбрал пользователь
        n = users[message.from_user.id]['subject_num'] = int(message.text) - 1
        users[message.from_user.id]['subject_path'] = subjects[n]['path']
        users[message.from_user.id]['subject'] = subjects[n]['name']
        s = "Выберете тему:\n"
        for t in range(0, len(subjects[n]['topics'])):
            s += f"{t + 1}. {subjects[n]['topics'][t]['name']}\n"
        msg = bot.send_message(message.chat.id, s)
        bot.register_next_step_handler(msg, f2_3)
        # просим указать тему

    except Exception as e:
        print(e)
        msg = bot.send_message(message.chat.id,
                               f'{e}\noooops, попробуйте еще раз..\n\nВведите /start для продолжения')


# Ожидаем тему
def f2_3(message):
    try:
        print(message.from_user.id, message.text, "f2_3")
        if message.content_type != "text":
            raise Exception("Ожидалось текстовое сообщение")
        if not message.text.isnumeric():
            raise Exception("Ожидалось число")
        if int(message.text) > len(subjects[users[message.from_user.id]['subject_num']]['topics']):
            raise Exception("Такой темы нет в списке")

        # запоминаем тему, которую выбрал пользователь
        users[message.from_user.id]['topic_num'] = int(message.text) - 1
        subject = users[message.from_user.id]['subject_num']
        users[message.from_user.id]['topic'] = subjects[subject]['topics'][int(message.text) - 1]['name']

        s = 'Начнем\n'
        s += 'Если Вы обнаружили ошибку в задании, напечатайте "Error"\n'
        s += 'Для остановки, напечатайте "End"\n\n'
        s += 'Удачи!\n'

        msg = bot.send_message(message.chat.id, s)
        f3_1(message)
        # переходим к решению задач

    except Exception as e:
        print(e)
        msg = bot.send_message(message.chat.id,
                               f'{e}\noooops, попробуйте еще раз..\n\nВведите /start для продолжения')


# Выбираем подходящую задачу
def f3_1(message):
    try:
        print(message.from_user.id, message.text, "f3_1")
        print(users)
        tg_user_id = message.from_user.id
        
        # тут вся магия подбора задачи для пользователя
        # передаем логин, предмет, тему
        # получаем id задачи, уровень сложности, кол-во решенных правильно этого уровня
        task_id, difficulty_level, count_correct_need = get_task_id(users[tg_user_id])
        
        if (task_id == None):
            raise Exception("Для Вас не нашлось задачи столь высокого уровня.. coming soon")

        # передаем предмет, id задачи
        # получаем условние, вложения, правильный ответ
        text, attachment, correct_answer = get_task_text(users[tg_user_id]['subject_path'], task_id)

        # запоминаем все данные про задачу
        users[message.from_user.id]['task'] = {}
        users[message.from_user.id]['task']['task_id'] = task_id
        users[message.from_user.id]['task']['difficulty_level'] = difficulty_level
        users[message.from_user.id]['task']['text'] = text
        users[message.from_user.id]['task']['count_correct_need'] = count_correct_need
        users[message.from_user.id]['task']['attachment'] = attachment
        users[message.from_user.id]['task']['correct_answer'] = correct_answer
        topic_num = users[message.from_user.id]['topic_num']

        # Формируем статус уровня
        s = ""
        s += f"Текущий уровень - {difficulty_level}\n"
        s += f"Для перехода на новый уровень осталось решить {count_correct_need} задач.\n\n"
        # добавляем текст
        s += text

        # отправляем
        msg = bot.send_message(message.chat.id, s)

        # регистрируем время начала
        users[message.from_user.id]['time_start'] = time.time()

        bot.register_next_step_handler(msg, f3_2)
        # ожидание ответа

    except Exception as e:
        print(e)
        msg = bot.send_message(message.chat.id,
                               f'{e}\noooops, попробуйте еще раз..\n\nВведите /start для продолжения')


# Ожидаем ответа на задачу
def f3_2(message):
    try:
        print(message.from_user.id, message.text, "f3_2")
        tg_user_id = message.from_user.id
        
        if message.content_type != "text":
            raise Exception("Ожидалось текстовое сообщение")
        if message.text == "Error":
            # увеличиваем счетчик ошибок в tasks
            update_errors_count(users[tg_user_id]['subject_path'], users[tg_user_id]['task']['task_id'])
            raise Exception("Сообщение об ошибке принято")
        if message.text == "End":
            raise Exception("Принято")

        # -увеличить счетчик использований в tasks
        if message.text == users[tg_user_id]['task']['correct_answer']:
            # -обработать и добавить в достижение +
            users[tg_user_id]["task_status"] = True # нужен для пометки решения
            msg = bot.send_message(message.chat.id, "+")
            # ответ правильный
        else:
            # -обработать и добавить в достижение -
            users[tg_user_id]["task_status"] = False # нужен для пометки не решения
            msg = bot.send_message(message.chat.id, "-")
            # ответ правильный

        insert_progress(users[tg_user_id])

        f3_1(message)

    except Exception as e:
        print(e)
        msg = bot.send_message(message.chat.id,
                               f'{e}\n попробуем еще раз..\n\nВведите /start для продолжения')


if __name__ == "__main__":
    start = time.time()
    print('start bot')
    bot.polling()
    print(time.time() - start)

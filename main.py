from settings import TOKEN
from utils import *

import time
import telebot

bot = telebot.TeleBot(TOKEN)

users = {}

# список доступных дисциплин
# Информатика
subjects = {0: {}}
subjects[0]['name'] = 'Информатика'
subjects[0]['path'] = 'tasks/inf.db'


# Для ускорения работы проанализируем список тем для каждого предмета
for subject in subjects.keys():
    subjects[subject]['topics'] = {}
    topics = get_topics(subjects[subject]['path'])
    topic_num = 0
    for topic, max_level in topics:
        subjects[subject]['topics'][topic_num] = {}
        subjects[subject]['topics'][topic_num]['name'] = topic
        subjects[subject]['topics'][topic_num]['max_level'] = max_level
        #еще можно находить кол-во задач для всех уровней для равномерности
        topic_num += 1
        


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
            #- деавторизуем, но надо другой командой. не тут
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
            #- тут надо деавторизовать предыдущего tg_user_id если такой есть, и написать ему сообщение, что он того.. 
            # авторизуем пользователя
            set_login_authorization(users[message.from_user.id]['login'], message.from_user.id)
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
        for i in range(0,len(subjects)):
            s += f"{i+1}. {subjects[i]['name']}\n"
            
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

        #запоминаем номер предмета, который выбрал пользователь
        n = users[message.from_user.id]['subject'] = int(message.text)-1
        
        
        s = "Выберете тему:\n"
        for t in range(0, len(subjects[n]['topics'])):
            s += f"{t+1}. {subjects[n]['topics'][t]['name']} \t{subjects[n]['topics'][t]['max_level']} макс. уровень\n"
        #for key, value in subjects[users[message.from_user.id]['subject']]['topics'].items():
        #    s += f'{key+1}. {value}\n'
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
        if int(message.text) > len(subjects[users[message.from_user.id]['subject']]['topics']):
            raise Exception("Такой темы нет в списке")
        
        #запоминаем тему, которую выбрал пользователь
        users[message.from_user.id]['topic_num'] = int(message.text)-1
        users[message.from_user.id]['topic'] = subjects[subject]['topics'][int(message.text)-1]['name']
        
        s = 'Начнем\n'
        s += 'Если Вы обнаружили ошибку в задании напечатайте "Error"\n'
        s += 'Для перехода к следующей модификации задания напечатайте "Next"\n'
        s += 'Для остановки напечатайте "End"\n\n'
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
        
        #передаем логин, предмет, тему
        #тут вся магия подбора задачи для пользователя
        task_id, difficulty_level = get_task_id(users[message.from_user.id]['login'],
                              subjects[users[message.from_user.id]['subject']]['path'],
                              users[message.from_user.id]['topic'])
        if (task_id == None):
            raise Exception("Для Вас не нашлось задачи столь высокого уровня.. coming soon")
        text, attachment, correct_answer = get_task_text(subjects[users[message.from_user.id]['subject']]['path'],task_id)


        #запоминаем все данные про задачу
        users[message.from_user.id]['task'] = {}
        users[message.from_user.id]['task']['task_id'] = task_id
        users[message.from_user.id]['task']['difficulty_level'] = difficulty_level
        users[message.from_user.id]['task']['text'] = text
        users[message.from_user.id]['task']['attachment'] = attachment
        users[message.from_user.id]['task']['correct_answer'] = correct_answer
        topic_num = users[message.from_user.id]['topic_num']

        
        s = f"Уровень: {difficulty_level}/{subjects[subject]['topics'][topic_num]['max_level']}\n\n"
        s += text
        msg = bot.send_message(message.chat.id, s)
        
        #регистрируем время начала
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
        if message.content_type != "text":
            raise Exception("Ожидалось текстовое сообщение")
        if message.text == "Error":
            # -увеличить счетчик ошибок в tasks
            raise Exception("Сообщение об ошибке принято")
        if message.text == "Exit":
            raise Exception("Принято")
        
        # -увеличить счетчик использований в tasks
        if message.text == users[message.from_user.id]['task']['correct_answer']:
            # -обработать и добавить в достижение +
            msg = bot.send_message(message.chat.id, "+")
            #ответ правильный
        else:
            # -обработать и добавить в достижение -
            msg = bot.send_message(message.chat.id, "-")
            #ответ правильный
            
        f3_1(message)
        
    except Exception as e:
        print(e)
        msg = bot.send_message(message.chat.id,
                               f'{e}\noooops, попробуйте еще раз..\n\nВведите /start для продолжения')



if __name__ == "__main__":
    start = time.time()
    print('start bot')
    bot.polling()
    print(time.time() - start)

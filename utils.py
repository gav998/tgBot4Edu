import sqlite3
import re
import random
import string
import base64 


from private.settings import TOKEN, ADMIN_ID

import os.path
import time
import telebot
import pandas


bot = telebot.TeleBot(TOKEN)



DB_SYS_PATH = './private/sys.db'
DB_LOG_PATH = './private/log.db'
PATH_TASKS = './private/tasks/'
PATH_TASKS_TEMP = './tmp/tasks/'

COUNT_CORRECT_4_NEXT_LEVEL = 3
CORRECT_ABOVE_INCORRECT_IN = 2
CRITICAL_COUNT_OF_ERROR_4_TASK = 5
MIN_TIME_2_TASK = 5

u = {}

# u[tg_id]['login']
# u[tg_id]['subject_num']
# u[tg_id]['subject_path']
# u[tg_id]['subject']
# u[tg_id]['topic_num']
# u[tg_id]['topic']
# u[tg_id]['task']['task_id']
# u[tg_id]['task']['difficulty_level']
# u[tg_id]['task']['text']
# u[tg_id]['task']['attachment']
# u[tg_id]['task']['correct_answer']
# u[tg_id]['time_start']
# u[tg_id]['time_end']
# u[tg_id]['task_status']
# u[tg_id]['answer']
# u[tg_id]['doc']

subjects = {}
# subjects[№]['topics'][№]['name']
# subjects[№]['topics'][№]['levels'][№]

def f1_1(u, tg_id):
    # если пользователь авторизован
    u[tg_id] = {}    
    login = get_login_authorization(tg_id)
    if login is not None:
        msg = bot.send_message(tg_id, f'Вы авторизованы под логином {login}')
        u[tg_id]['login'] = login
        u[tg_id]['route'] = 'f2_1'
        u[tg_id]['wait'] = False
    else:
        # просим указать номер по списку в ЭЖД
        s = ''
        s += f'Для старта укажите идентификационный код:\n\n'
        s += f'(номер класса)(буква класса)_(номер по списку в ЭЖД)\n\n'
        s += f'Например, для ученика 7Б класса под номером 11 в ЭЖД, '
        s += f'идентификационный код будет таким: 7Б_11\n'
        msg = bot.send_message(tg_id, s)

        # ожидаем номера ЭЖД
        u[tg_id]['route'] = 'f1_2'
        u[tg_id]['wait'] = True

# ожидаем номер ЭЖД
def f1_2(u, tg_id,text):
    if not (check_re(text) or check_re_t(text)):
        raise Exception("Неправильный формат идентификационного кода")
    u[tg_id]['login'] = text

    # если такой пользователь существует, то и пароль у него существует
    password = get_password(text)
    if password is not None:
        msg = bot.send_message(tg_id,
                               f"Такой пользователь уже зарегистрирован!\n\nВведите, пожалуйста, пароль:\n")
        # ожидаем пароль пользователя
        u[tg_id]['route'] = 'f1_3'
        u[tg_id]['wait'] = True
    # иначе
    else:
        # генерируем пароль новому пользователю
        password = random_pass()
        # сохраняем его пароль
        create_user(text, password)
        # сообщаем ученику его пароль
        if check_re(text):
            msg = bot.send_message(tg_id, f'Тебе назначен пароль:\n')
            msg = bot.send_message(tg_id, password)
            # авторизуем пользователя
            set_login_authorization(text, tg_id)
            # отправляем его в функцию выбора предмета
            u[tg_id]['route'] = 'f2_1'
            u[tg_id]['wait'] = False
        else:
            s = f"Пользователю {text} назначен пароль {password}\n"
            for tg_admin in ADMIN_ID:
                msg = bot.send_message(tg_admin, s)
            msg = bot.send_message(tg_id,
                               f"Пароль направлен администратору ресурса!\n\nВведите, пожалуйста, пароль:\n")
            # ожидаем пароль пользователя
            u[tg_id]['route'] = 'f1_3'
            u[tg_id]['wait'] = True

# ожидаем пароль
def f1_3(u, tg_id,text):
    # сверка паролей    
    password = get_password(u[tg_id]['login'])
    if text == password:
        # деавторизовать предыдущего tg_id если такой есть, и написать ему сообщение, что он того..
        prev_id = get_id_authorization(u[tg_id]['login'])
        if prev_id is not None:
            set_login_deauthorization(u[tg_id]['login'])
            msg = bot.send_message(prev_id, f'Выполнен вход с другого устройства')
        
        # авторизуем пользователя
        set_login_authorization(u[tg_id]['login'], tg_id)
        msg = bot.send_message(tg_id, f'Успешно')
        # отправляем его в функцию выбора предмета
        u[tg_id]['route'] = 'f2_1'
        u[tg_id]['wait'] = False
    else:
        raise Exception("Пароль не совпал")


# предлагаем список предметов
def f2_1(u, tg_id):
    s = "Доступен выбор предмета. Укажите только номер:\n"
    for i in range(0, len(subjects)):
        s += f"{i + 1}. {subjects[i]['name']}\n"

    msg = bot.send_message(tg_id, s)
    u[tg_id]['route'] = 'f2_2'
    u[tg_id]['wait'] = True


# ожидаем выбор предмета и запрашиваем тему
def f2_2(u, tg_id, text):
    if not text.isnumeric():
        raise Exception("Ожидалось число")
    if int(text) > len(subjects):
        raise Exception("Такого предмета нет в списке")

    # запоминаем номер предмета, который выбрал пользователь
    n = u[tg_id]['subject_num'] = int(text) - 1
    u[tg_id]['subject_path'] = subjects[n]['path']
    u[tg_id]['subject'] = subjects[n]['name']

    # генерируем список тем
    s = ""
    for t in range(0, len(subjects[n]['topics'])):
        s += f"{t + 1}. {subjects[n]['topics'][t]['name']}\n"
    
    # если тем нет
    if s == "":
        raise Exception("Темы еще не добавлены.")
        
    msg = bot.send_message(tg_id, f"Выберете тему:\n{s}")
    
    # запрашиваем тему
    u[tg_id]['route'] = 'f2_3'
    u[tg_id]['wait'] = True


# Ожидаем тему
def f2_3(u, tg_id, text):
    if not text.isnumeric():
        raise Exception("Ожидалось число")
    
    subject = u[tg_id]['subject_num']
    if int(text) > len(subjects[subject]['topics']):
        raise Exception("Такой темы нет в списке")

    # запоминаем тему, которую выбрал пользователь
    topic = u[tg_id]['topic_num'] = int(text) - 1
    u[tg_id]['topic'] = subjects[subject]['topics'][topic]['name']
    
    
    if (check_re_t(u[tg_id]['login'])):
        # если это учитель, то формируем статистику
        s = "Если Вы хотите запросить статистику выполнения заданий темы для класса, пожалуйста, введите номер и букву класса. Например,\n 7А\n\n"
        msg = bot.send_message(tg_id, s)
        u[tg_id]['route'] = 'result_class'
        u[tg_id]['wait'] = True 
    else:
        # переходим к решению задач
        u[tg_id]['route'] = 'f3_0'
        u[tg_id]['wait'] = False 
            

# обучение по теме
def f3_0(u, tg_id):
    s = 'Начнем\n'
    s += 'Если Вы обнаружили ошибку в задании, напечатайте "/error"\n'
    s += 'Для остановки, напечатайте "/end"\n\n'
    s += 'Удачи!\n'
    msg = bot.send_message(tg_id, s)
    u[tg_id]['route'] = 'f3_1'
    u[tg_id]['wait'] = False 


# выбираем подходящую задачу
def f3_1(u, tg_id):
    # тут вся магия подбора задачи для пользователя
    # передаем логин, предмет, тему
    # получаем id задачи, уровень сложности, кол-во решенных правильно этого уровня
    task_id, difficulty_level, count_correct_need = get_task_id(u[tg_id])
    
    if (task_id == None):
        raise Exception("Для Вас не нашлось задачи столь высокого уровня.. coming soon")

    # передаем предмет, id задачи
    # получаем условние, вложения, правильный ответ
    text, attachment, correct_answer = get_task_text(u[tg_id]['subject_path'], task_id)

    # запоминаем все данные про задачу
    u[tg_id]['task'] = {}
    u[tg_id]['task']['task_id'] = task_id
    u[tg_id]['task']['difficulty_level'] = difficulty_level
    u[tg_id]['task']['text'] = text
    u[tg_id]['task']['count_correct_need'] = count_correct_need
    u[tg_id]['task']['attachment'] = attachment
    u[tg_id]['task']['correct_answer'] = correct_answer

    # формируем статус уровня
    s = ""
    s += f"Текущий уровень - {difficulty_level}\n"
    s += f"Для перехода на новый уровень осталось решить задач: {count_correct_need}\n\n"
    # добавляем текст
    s += text
    
    # отправляем
    msg = bot.send_message(tg_id, s)
    if(not attachment is None)and(len(attachment)>50):
        png_recovered = base64.b64decode(attachment)
        photo = open(f"./tmp/{u[tg_id]['login']}.png", 'wb')
        photo.write(png_recovered)
        photo.close()
        photo = open(f"./tmp/{u[tg_id]['login']}.png", 'rb')
        msg = bot.send_photo(tg_id, photo)

    # регистрируем время начала
    u[tg_id]['time_start'] = time.time()

    # ожидание ответа
    u[tg_id]['route'] = 'f3_2'
    u[tg_id]['wait'] = True 

# Ожидаем ответа на задачу
def f3_2(u, tg_id, text):
    if text == "/error":
        # увеличиваем счетчик ошибок в tasks и achivements
        update_errors_count(u[tg_id])
        raise Exception("Сообщение об ошибке принято")
    if text == "/end":
        raise Exception("Принято")
    
    # регистрируем время ответа
    u[tg_id]['time_end'] = time.time()
    if u[tg_id]['time_end'] - u[tg_id]['time_start'] < MIN_TIME_2_TASK:
        raise Exception(f"Пожалуйста, внимательно читайте условие!!!\n(не менее {MIN_TIME_2_TASK} секунд)")

    # запоминаем ответ
    u[tg_id]['answer'] = text
    if text == u[tg_id]['task']['correct_answer']:
        # если ответ правильный
        # обработать и добавить в достижение +
        u[tg_id]["task_status"] = True
        msg = bot.send_message(tg_id, "+")
    else:
        # иначе
        # обработать и добавить в достижение -
        u[tg_id]["task_status"] = False
        msg = bot.send_message(tg_id, "-")
        # ответ правильный
        
    insert_progress(u[tg_id], tg_id)

    u[tg_id]['route'] = 'f3_1'
    u[tg_id]['wait'] = False 


# Формирование отчета-статистики по теме
# Ожидаем номер класса, для которого надо сформировать статистику по теме
def result_class(u, tg_id, text):
    if not 'subject' in u[tg_id]:
        raise Exception(f"Не выбран предмет")
    if not 'topic' in u[tg_id]:
        raise Exception(f"Не выбрана тема")
 
    group = text
    # Формируем первую таблицу
    s = get_result_1(u[tg_id], group)
    msg = bot.send_message(tg_id, s, parse_mode="markdown")
    
    s = "Для повторного формирования отчета, напишите /start\n"
    s += "Вы можете продолжить решать задачи по предмету.\n"
    msg = bot.send_message(tg_id, s)

    # Формируем вторую таблицу
    #s = get_result_2(u[tg_id], group)
    #msg = bot.send_message(tg_id, s)

    # переходим к решению задач
    u[tg_id]['route'] = 'f3_0'
    u[tg_id]['wait'] = False 

#проверяем корректность таблицы excel
def check_tasks(doc):
    name_split = split_file_name(doc.file_name)
    
    # в названии должно быть 5 аргументов
    if len(name_split) != 5:
        raise Exception(f"Ожидалось 5 аргументов в названии: \n\nПредмет+Класс+Тема+Уровень.xlsx\n\nТекущий формат: \n{name_split}\n")
    
    # предмет должен существовать
    is_subject(name_split[0])
        
    # номер класса должен быть цифрой
    if not name_split[1].isdigit():
        raise Exception(f"Номер класса должен быть цифрой: {name_split[1]}\n")

    # номер уровня должен быть цифрой
    if not name_split[3].isdigit():
        raise Exception(f"Номер уровня должен быть цифрой: {name_split[3]}\n")    
        
    # расширение файла должно быть *.xlsx
    if name_split[4] != 'xlsx':
        raise Exception(f"Расширение файла должно быть *.xlsx: {name_split[4]}\n")
    
    # проверяем существование файла
    if os.path.exists(f'{PATH_TASKS}{doc.file_name}'):
        raise Exception(f"Файл {doc.file_name} уже существует.\nПопробуйте увеличить уровень")
    
    return True

def promt_add_tasks(u, tg_id, doc):
    # скачиваем файл
    file_info = bot.get_file(doc.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    FULL_PATH = f'{PATH_TASKS_TEMP}{doc.file_name}'
    with open(FULL_PATH, 'wb') as new_file:
        new_file.write(downloaded_file)

    # парсим одну задачу
    name_split = split_file_name(doc.file_name)
    u[tg_id]['doc_file'] = xlsx = pandas.read_excel(FULL_PATH)
    print('Отладка ',xlsx.columns)
    if (len(xlsx.columns)) < 3:
        raise Exception(f"В файле должно быть минимум 3 столбца: Текст задачи | Фото (base64 encode) | Правильный ответ\n")
    
    # уточняем у пользователя корректность
    s = ""
    s += f"Предмет: {name_split[0]}\n"
    s += f"Класс: {name_split[1]}\n"
    s += f"Тема: {name_split[2]}\n"
    s += f"Уровень: {name_split[3]}\n"
    s += f"Кол-во задач в таблице: {len(xlsx[xlsx.columns[0]])}\n"
    s += f"Пример задачи:\n"
    s += f"{xlsx[xlsx.columns[0]][0]}\n\n"
    s += f"Ответ: "
    s += f"{xlsx[xlsx.columns[2]][0]}\n\n"
    s += f"Добавить задачи в таблицу?\n1.Да\n0.Нет\n"

    
    attachment = f'{xlsx[xlsx.columns[1]][0]}'
    if(not attachment is None)and(len(attachment)>50):
        png_recovered = base64.b64decode(attachment)
        photo = open(f"./tmp/{u[tg_id]['login']}.png", 'wb')
        photo.write(png_recovered)
        photo.close()
        photo = open(f"./tmp/{u[tg_id]['login']}.png", 'rb')
        msg = bot.send_photo(tg_id, photo)

    msg = bot.send_message(tg_id, s)

    u[tg_id]['route'] = 'add_tasks'
    u[tg_id]['wait'] = True 


def add_tasks(u, tg_id, text):
    global subjects
    if text == '1':
        doc = u[tg_id]['doc']
        
        name_split = split_file_name(doc.file_name)

        # предмет должен существовать
        subject = is_subject(name_split[0])
        
        insert_xlsx(subjects[subject]['path'],name_split, u[tg_id]['doc_file'])
        
        os.rename(f'{PATH_TASKS_TEMP}{doc.file_name}', f'{PATH_TASKS}{doc.file_name}')
        
        subjects = get_subjects()
        
        for tg_admin_id in ADMIN_ID:
            msg = bot.send_message(tg_admin_id, f"Пользователь {get_login_authorization(tg_id)} добавил {name_split}")
        
        raise Exception(f"Выполнено\n")
    else: 
        FULL_PATH = f"{PATH_TASKS_TEMP}{u[tg_id]['doc'].file_name}"
        os.remove(FULL_PATH)
        raise Exception(f"Отменено\n")


def is_subject(s):
    subject = None
    for i in subjects:
        if s in subjects[i]['name']:
            subject = i
            break
    if (subject is None):
        raise Exception(f"Такого предмета в БД не зарегистрировано: {s}\n")
    return subject

def get_login_authorization(tg_user_id):
    with sqlite3.connect(DB_SYS_PATH) as db:
        sql = "SELECT logins FROM list_of_authorizations WHERE tg_user_ids = ?;"
        for login in db.execute(sql, (tg_user_id,)):
            return login[0]
    return None


def get_id_authorization(login):
    with sqlite3.connect(DB_SYS_PATH) as db:
        sql = "SELECT tg_user_ids FROM list_of_authorizations WHERE logins = ?;"
        for _id in db.execute(sql, (login,)):
            return _id[0]
    return None


def set_login_authorization(login, tg_user_id):
    with sqlite3.connect(DB_SYS_PATH) as db:
        sql = "INSERT INTO list_of_authorizations(logins, tg_user_ids) VALUES(?, ?);"
        db.execute(sql, (login, tg_user_id,))


def set_login_deauthorization(login):
    with sqlite3.connect(DB_SYS_PATH) as db:  
        sql = "DELETE FROM list_of_authorizations WHERE logins = ?"
        db.execute(sql, (login, )) 


def reset_password(tg_id, login):
    with sqlite3.connect(DB_SYS_PATH) as db:  
        sql = "DELETE FROM login_password WHERE logins = (?)"
        db.execute(sql, (login, ))
        sql = "DELETE FROM list_of_authorizations WHERE logins = (?)"
        db.execute(sql, (login, )) 
    for tg_admin_id in ADMIN_ID:
        msg = bot.send_message(tg_admin_id, f"Пользователь {login} удален пользователем {get_login_authorization(tg_id)}")
    msg = bot.send_message(tg_id, f"Пользователь {login} удален")
        

def get_password(login):
    with sqlite3.connect(DB_SYS_PATH) as db:
        sql = "SELECT passwords FROM login_password WHERE logins = ?;"
        for password in db.execute(sql, (login,)):
            return password[0]
    return None


def create_user(login, password):
    with sqlite3.connect(DB_SYS_PATH) as db:
        sql = "INSERT INTO login_password(logins, passwords) VALUES(?, ?);"
        db.execute(sql, (login, password,))


def get_topics(path):
    with sqlite3.connect(path) as db:
        sql = "SELECT DISTINCT topics FROM tasks ORDER BY topics;"
        return db.execute(sql)


def get_task_id(user_data: dict):
    # Определим текущий уровень ученика
    difficulty_level = count_correct = count_incorrect = 0
    with sqlite3.connect(DB_SYS_PATH) as db:
        # находим текущий уровень для данной темы
        sql = f"SELECT difficulty_levels, count_correct, count_incorrect FROM achivements WHERE logins = ? AND subjects = ? AND topics = ? ORDER BY difficulty_levels DESC;"
        for _difficulty_level, _count_correct, _count_incorrect in db.execute(sql, (user_data['login'], user_data['subject'], user_data['topic'],)):
            difficulty_level = _difficulty_level
            count_correct = _count_correct
            count_incorrect = _count_incorrect
            break

        # если данную тему ученик ранее не проходил, создадим запись с темой
        if difficulty_level == 0:
            sql = f"INSERT INTO achivements(logins, subjects, topics) VALUES(?, ?, ?);"
            db.execute(sql, (user_data['login'], user_data['subject'], user_data['topic'],))
            difficulty_level = 1
        # проверяем, можем ли перейти на новый уровень
        if count_correct > COUNT_CORRECT_4_NEXT_LEVEL-1: 
            difficulty_level += 1
            count_correct = 0
            count_incorrect = 0
            # ОБНОВИТЬ БД! Иначе дальше 2 уровня не продвинемся 
            sql = f"INSERT INTO achivements(logins, subjects, topics, difficulty_levels) VALUES(?, ?, ?, ?);"
            db.execute(sql, (user_data['login'], user_data['subject'], user_data['topic'], difficulty_level,))

    # можно дополнительно проверять существует ли след уровень, если нет, то не повышать

    # Найти задачу подходящего уровня
    with sqlite3.connect(user_data['subject_path']) as db:
        sql = "SELECT ids, count_errors FROM tasks WHERE topics = ? AND difficulty_levels = ? ORDER BY count_uses;"
        for _id, _count_error in db.execute(sql, (user_data['topic'], difficulty_level,)):
            # проверять кол-во репортов на задачу и не выдавать такие
            if _count_error > CRITICAL_COUNT_OF_ERROR_4_TASK:
                continue
                
            # - Успешно решенные не предлагать
            # - в логах проверять логин и id и статус, если есть, увеличивать каунтер использований и искать следующую
            # - для этого надо реализовать логи
            with sqlite3.connect(DB_LOG_PATH) as db2:
                sql = "SELECT id FROM log WHERE logins = (?) AND subjects = (?) AND task_ids = (?) AND task_statuses = (?);"
                solved = db2.execute(sql, (user_data['login'], user_data['subject'],_id, True,)).fetchone()
                if solved is not None:
                    continue

            return _id, difficulty_level, COUNT_CORRECT_4_NEXT_LEVEL - count_correct
    return None, None, None


def get_task_text(path, task_id):
    with sqlite3.connect(path) as db:
        sql = f"UPDATE tasks SET count_uses = count_uses + 1 WHERE ids = (?)"
        db.execute(sql, (task_id,))
        sql = "SELECT texts, attachments, answers FROM tasks WHERE ids = ?;"
        for text, attachment, answer in db.execute(sql, (task_id,)):
            return text, attachment, answer


def update_errors_count(user_data: dict):
    with sqlite3.connect(user_data['subject_path']) as db:
        sql = "UPDATE tasks SET count_errors = count_errors + 1 WHERE ids=(?)"
        db.execute(sql, (user_data['task']['task_id'],))
        
    with sqlite3.connect(DB_SYS_PATH) as db:
        sql = f"UPDATE achivements SET count_error = count_error + 1 WHERE logins = (?) AND subjects = (?) AND topics = (?) AND difficulty_levels = (?)"
        db.execute(sql, (user_data['login'], user_data['subject'], user_data['topic'], user_data['task']['difficulty_level'],))


def insert_progress(user_data: dict, tg_id):
    with sqlite3.connect(DB_SYS_PATH) as db:
        if user_data["task_status"]:
            sql = f"UPDATE achivements SET count_correct = count_correct + 1 WHERE logins = (?) AND subjects = (?) AND topics = (?) AND difficulty_levels = (?)"
        else:
            sql = f"UPDATE achivements SET count_incorrect = count_incorrect + 1 WHERE logins = (?) AND subjects = (?) AND topics = (?) AND difficulty_levels = (?)"
        db.execute(sql, (user_data['login'], user_data['subject'], user_data['topic'], user_data['task']['difficulty_level'],))
        
    with sqlite3.connect(DB_LOG_PATH) as db:
        sql = f"INSERT INTO log(time_ends, logins, tg_ids, subjects, topics, difficulty_levels, task_ids, answers, task_statuses, time_deltas)"
        sql += "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
        db.execute(sql, (user_data['time_end'],
                         user_data['login'],
                         tg_id,
                         user_data['subject'],
                         user_data['topic'],
                         user_data['task']['difficulty_level'],
                         user_data['task']['task_id'],
                         user_data['answer'],
                         user_data['task_status'],
                         user_data['time_end'] - user_data['time_start'],))

def create_tasks(subjects):
    sql = """
    CREATE TABLE IF NOT EXISTS tasks (
    ids               INTEGER PRIMARY KEY AUTOINCREMENT
                              UNIQUE,
    classes           INTEGER DEFAULT (9) 
                              NOT NULL,
    topics            TEXT    NOT NULL,
    difficulty_levels INTEGER NOT NULL
                              DEFAULT (1),
    texts             TEXT    NOT NULL,
    attachments       TEXT,
    answers           TEXT    NOT NULL,
    count_uses        INTEGER DEFAULT (0) 
                              NOT NULL,
    count_errors      INTEGER NOT NULL
                              DEFAULT (0) );"""
    for subject in subjects.keys():
        with sqlite3.connect(subjects[subject]['path']) as db:
            db.execute(sql)
        

def random_pass():
    pass_w = ""
    for i in range(6):
        if random.randint(0, 1) == 1:
            pass_w += str(random.randint(0, 9))
        else:
            pass_w += random.choice(string.ascii_uppercase)
    return pass_w


def check_re(text):
    regexp = r"(^\d+[А-ЯЁ]_\d*)"
    matches = re.match(regexp, text)
    if matches is not None:
        return True
    else:
        return False



def check_re_t(text):
    regexp = r"(^TEACHER_\d*)"
    matches = re.match(regexp, text)
    if matches is not None:
        return True
    else:
        return False


def get_result_1(user_data: dict, group):
    res = {}
    with sqlite3.connect(DB_SYS_PATH) as db:
        # - надо безопаснее..
        sql = f"""SELECT logins,difficulty_levels,count_correct,count_incorrect,count_error,viewed
        FROM achivements 
        WHERE logins LIKE '{group}%'
        AND subjects = (?)
        AND topics = (?);"""
        for login, lvl, correct, incorrect, error, viewed in db.execute(sql, (user_data['subject'], user_data['topic'],)):
            num = 0
            if login[len(group)+1:].isdigit():
                num = int(login[len(group)+1:])
            else:
                num = login
            if not num in res:
                res[num] = {}
            res[num][lvl] = {}
            res[num][lvl]['correct'] = correct
            res[num][lvl]['incorrect'] = incorrect
            res[num][lvl]['error'] = error
            res[num][lvl]['viewed'] = viewed
        sql = f"""UPDATE achivements SET viewed = True WHERE logins LIKE '{group}%'
        AND subjects = (?)
        AND topics = (?);"""
        db.execute(sql, (user_data['subject'], user_data['topic'],))
    s = f"Статистика сформирована для класса {group} "
    s += f"по предмету {user_data['subject']}, "
    s += f"по теме {user_data['topic']}\n\n"
    s += f"Формат: номер ученика | кол-во решенных задач 1 уровня, 2 уровня, ..\n\n"
    # надо сортировать учеников по возрастанию
    for i in sorted(res.keys()):
        s += f'{i} | '
        # можно не сортировать сложность по возрастанию (уже)
        for j in sorted(res[i].keys()):
            #s += f"{res[i][j]['correct']}/{res[i][j]['incorrect']}/{res[i][j]['error']}|"
            if res[i][j]['viewed']:
                s += f"{res[i][j]['correct']}, "
            else:
                s += f"*{res[i][j]['correct']}*, "
        s += f'\n'
    return s


def split_file_name(file_name):
    return file_name.replace("_", " ").replace("+", ".").split('.')
 
    
def insert_xlsx(path, name, xlsx):
    with sqlite3.connect(path) as db:
        count = 0
        sql = "INSERT INTO tasks(classes, topics, difficulty_levels, texts, attachments, answers) "
        sql += "VALUES(?, ?, ?, ?, ?, ?);"
        for i in range(0, len(xlsx[xlsx.columns[0]])):
            text = str(xlsx[xlsx.columns[0]][i])
            attachment = str(xlsx[xlsx.columns[1]][i])
            answer = str(xlsx[xlsx.columns[2]][i])
            print("insert_xlsx", count, text)
            if (not "nan" in [text, answer]) and (len(text)>5):
                db.execute(sql,(name[1],name[2],name[3], text,attachment,answer,))
                count += 1
        print(f"/nДобавлено {count} записей в /n{path}/n{name}/n")
    

# список доступных дисциплин
def get_subjects():
    subjects = {}

    i = len(subjects) 
    subjects[i] = {}
    subjects[i]['name'] = 'Математика'
    subjects[i]['path'] = './private/subject_math.db'
    
    i = len(subjects) 
    subjects[i] = {}
    subjects[i]['name'] = 'Информатика'
    subjects[i]['path'] = './private/subject_inf.db'
    
    i = len(subjects) 
    subjects[i] = {}
    subjects[i]['name'] = 'Русский язык'
    subjects[i]['path'] = './private/subject_rus.db'
    
    i = len(subjects) 
    subjects[i] = {}
    subjects[i]['name'] = 'Физика'
    subjects[i]['path'] = './private/subject_physics.db'
    
    i = len(subjects) 
    subjects[i] = {}
    subjects[i]['name'] = 'Обществознание'
    subjects[i]['path'] = './private/subject_society.db'

    i = len(subjects) 
    subjects[i] = {}
    subjects[i]['name'] = 'История'
    subjects[i]['path'] = './private/subject_history.db'
    
    i = len(subjects) 
    subjects[i] = {}
    subjects[i]['name'] = 'Химия'
    subjects[i]['path'] = './private/subject_chemistry.db'  

    i = len(subjects) 
    subjects[i] = {}
    subjects[i]['name'] = 'Биология'
    subjects[i]['path'] = './private/subject_biology.db'     
    
    i = len(subjects) 
    subjects[i] = {}
    subjects[i]['name'] = 'Английский язык'
    subjects[i]['path'] = './private/subject_english.db'      
    
    create_tasks(subjects)
    # Для ускорения работы проанализируем список тем для каждого предмета
    for subject in subjects.keys():
        subjects[subject]['topics'] = {}
        topics = get_topics(subjects[subject]['path'])
        topic_num = 0
        for topic in topics:
            subjects[subject]['topics'][topic_num] = {}
            subjects[subject]['topics'][topic_num]['name'] = topic[0]
            #subjects[subject]['topics'][topic_num]['max_level'] = max_level
            # - еще можно находить кол-во задач для всех уровней для равномерности
            topic_num += 1
    return subjects
    
subjects = get_subjects()




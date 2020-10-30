import sqlite3
import re
import random
import string

DB_SYS_PATH = 'sys.db'
DB_SCORES_PATH = 'scores.db'

COUNT_CORRECT_4_NEXT_LEVEL = 10
CORRECT_ABOVE_INCORRECT_IN = 2
CRITICAL_COUNT_OF_ERROR_4_TASK = 5


def get_login_authorization(tg_user_id):
    with sqlite3.connect(DB_SYS_PATH) as db:
        sql = "SELECT logins FROM list_of_authorizations WHERE tg_user_ids = ?;"
        for login in db.execute(sql, (tg_user_id,)):
            return login[0]
    return None


def set_login_authorization(login, tg_user_id):
    with sqlite3.connect(DB_SYS_PATH) as db:
        sql = "INSERT INTO list_of_authorizations(logins, tg_user_ids) VALUES(?, ?);"
        db.execute(sql, (login, tg_user_id,))


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
        sql = "SELECT DISTINCT topics, difficulty_levels FROM tasks ORDER BY topics ASC, difficulty_levels DESC;"
        return db.execute(sql)


def get_task_id(login, path, topic):
    #Определим текущий уровень ученика
    difficulty_level = count_correct = count_incorrect = 0
    with sqlite3.connect(DB_SCORES_PATH) as db:
        #создаем таблицу достижений ученика, если ее не существует
        #надо сделать безопаснее, но как?..
        sql = f"""CREATE TABLE IF NOT EXISTS T{login}_achivements (
        ids INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        subjects INTEGER NOT NULL,
        topics TEXT NOT NULL,
        difficulty_levels INTEGER NOT NULL DEFAULT (1),
        count_correct INTEGER NOT NULL DEFAULT (0),
        count_incorrect INTEGER NOT NULL DEFAULT (0)
        );"""
        db.execute(sql)
        #находим текущий уровень для данной темы
        sql = f"SELECT difficulty_levels, count_correct, count_incorrect FROM T{login}_achivements WHERE subjects = ? AND topics = ? ORDER BY difficulty_levels DESC;"
        
        for _difficulty_level, _count_correct, _count_incorrect in db.execute(sql, (path, topic,)):
            difficulty_level = _difficulty_level
            count_correct = count_correct
            count_incorrect = _count_incorrect
            break
        #если данную тему ученик ранее не проходил, создадим запись с темой
        if difficulty_level == 0:
            sql = f"INSERT INTO T{login}_achivements(subjects, topics) VALUES(?, ?);"
            db.execute(sql, (path, topic,))
            difficulty_level = 1
    #проверяем, можем ли перейти на новый уровень
    if (count_correct > COUNT_CORRECT_4_NEXT_LEVEL) and (count_correct > count_correct * CORRECT_ABOVE_INCORRECT_IN):
        difficulty_level += 1
    # можно дополнительно проверять существует ли след уровень, если нет, то не повышать
    
    #Найти задачу подходящего уровня
    with sqlite3.connect(path) as db:
        sql = "SELECT ids, count_errors FROM tasks WHERE topics = ? AND difficulty_levels = ? ORDER BY count_uses;"
        for _id, _count_error in db.execute(sql, (topic, difficulty_level,)):
            if _count_error > CRITICAL_COUNT_OF_ERROR_4_TASK:
                continue
        #еще можно проверять кол-во репортов на задачу и не выдавать такие
            return _id, difficulty_level
    return None, None
    
    #найти задачу с данной темой и уровнем с наименьшим кол-вом использований
    #если репортов меньше 5: return id
    

    #with sqlite3.connect(path) as db:
    #    sql = "SELECT DISTINCT topics FROM tasks;"
    #    return db.execute(sql)

def get_task_text(path, task_id):
    with sqlite3.connect(path) as db:
        sql = "SELECT texts, attachments, answers FROM tasks WHERE ids = ?;"
        for text, attachment, answer in db.execute(sql,(task_id,)):
            return text, attachment, answer

def check_answer(path, task_id):
    with sqlite3.connect(path) as db:
        #sql = "SELECT DISTINCT topics FROM tasks;"
        return db.execute(sql)
        
        
def insert_progress(path, user_data: dict):
    # тут должна быть вызвона функция получения задания
    # get_task_id()
    with sqlite3.connect(path) as db:
        sql = "INSERT INTO user_progress(logins, classes, topic, subject, id_tasks, status, time_start, time_stop) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?);"
        res = db.execute(sql, *user_data)
        print(res)


def random_pass():
    pass_w = ""
    for i in range(6):
        if random.randint(0, 1) == 1:
            pass_w += str(random.randint(0, 9))
        else:
            pass_w += random.choice(string.ascii_uppercase)
    return pass_w


def check_re(text):
    regexp = r"(^\d+\w_\d*)"
    matches = re.match(regexp, text)
    if matches is not None:
        return True
    else:
        return False

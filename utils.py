import sqlite3
import re
import random
import string

DB_SYS_PATH = 'sys.db'

COUNT_CORRECT_4_NEXT_LEVEL = 3
CORRECT_ABOVE_INCORRECT_IN = 2
CRITICAL_COUNT_OF_ERROR_4_TASK = 5


# список доступных дисциплин
def get_subjects():
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
            # - еще можно находить кол-во задач для всех уровней для равномерности
            topic_num += 1
    return subjects


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
        if count_correct > COUNT_CORRECT_4_NEXT_LEVEL: 
            difficulty_level += 1
            count_correct = 0
            count_incorrect = 0
            # ОБНОВИТЬ БД! Иначе дальше 2 уровня не продвинемся 
            sql = f"INSERT INTO achivements(logins, subjects, topics, difficulty_levels) VALUES(?, ?, ?, ?);"
            db.execute(sql, (user_data['login'], user_data['subject'], user_data['topic'], difficulty_level,))

    # - можно дополнительно проверять существует ли след уровень, если нет, то не повышать

    # Найти задачу подходящего уровня
    with sqlite3.connect(user_data['subject_path']) as db:
        sql = "SELECT ids, count_errors FROM tasks WHERE topics = ? AND difficulty_levels = ? ORDER BY count_uses;"
        for _id, _count_error in db.execute(sql, (user_data['topic'], difficulty_level,)):
            # проверять кол-во репортов на задачу и не выдавать такие
            if _count_error > CRITICAL_COUNT_OF_ERROR_4_TASK:
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


def update_errors_count(path, task_id: int):
    with sqlite3.connect(path) as db:
        sql = "UPDATE tasks SET count_errors = count_errors + 1 WHERE ids=(?)"
        db.execute(sql, (task_id,))


def update_errors_count2(user_data: dict):
    with sqlite3.connect(DB_SYS_PATH) as db:
        sql = f"UPDATE achivements SET count_error = count_error + 1 WHERE logins = (?) AND subjects = (?) AND topics = (?) AND difficulty_levels = (?)"
        db.execute(sql, (user_data['login'], user_data['subject'], user_data['topic'], user_data['task']['difficulty_level'],))


def insert_progress(user_data: dict):
    with sqlite3.connect(DB_SYS_PATH) as db:
        if user_data["task_status"]:
            sql = f"UPDATE achivements SET count_correct = count_correct + 1 WHERE logins = (?) AND subjects = (?) AND topics = (?) AND difficulty_levels = (?)"
        else:
            sql = f"UPDATE achivements SET count_incorrect = count_incorrect + 1 WHERE logins = (?) AND subjects = (?) AND topics = (?) AND difficulty_levels = (?)"
        db.execute(sql, (user_data['login'], user_data['subject'], user_data['topic'], user_data['task']['difficulty_level'],))


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
    regexp = r"(^teacher_\d*)"
    matches = re.match(regexp, text)
    if matches is not None:
        return True
    else:
        return False

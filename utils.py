import sqlite3
import re
import random
import string

from settings import DB_SYS_PATH

def get_login_authorization(tg_user_id):
    with sqlite3.connect(DB_SYS_PATH) as db:
        sql = f"SELECT logins FROM list_of_authorizations WHERE tg_user_ids = ?;"
        for login in db.execute(sql,(tg_user_id,)):
            return login[0]
    return None


def set_login_authorization(login, tg_user_id):  
    with sqlite3.connect(DB_SYS_PATH) as db:
        sql = "INSERT INTO list_of_authorizations(logins, tg_user_ids) VALUES(?, ?);"
        db.execute(sql, (login, tg_user_id,))


def get_password(login):  
    with sqlite3.connect(DB_SYS_PATH) as db:
        sql = f"SELECT passwords FROM login_password WHERE logins = ?;"
        for password in db.execute(sql, (login,)):
            return password[0]
    return None


def create_user(login, password):  
    with sqlite3.connect(DB_SYS_PATH) as db:
        sql = "INSERT INTO login_password(logins, passwords) VALUES(?, ?);"
        db.execute(sql, (login, password,))

def get_topics(path):
    with sqlite3.connect(path) as db:
        sql = f"SELECT DISTINCT topics FROM tasks;"
        return db.execute(sql)

def get_task_id(path, topic):
    with sqlite3.connect(path) as db:
        sql = f"SELECT DISTINCT topics FROM tasks;"
        return db.execute(sql)

def random_pass():
    pass_w = ""
    for i in range(6):
        if random.randint(0, 1) == 1:
            pass_w += str(random.randint(0,9))
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
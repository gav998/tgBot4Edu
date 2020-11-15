from utils import *
import traceback

# только текстовые сообщения
@bot.message_handler(func=lambda m: True)
def router(m):
    # пользователь
    tg_id = m.chat.id
    global u
    global subjects
    
    try:
        # сообщение
        text = m.text
        
        # отладка
        if tg_id in u:
            print(u[tg_id], text)
        else:
            print(tg_id, text, "router")
        
        # админка. сброс текущей сессии
        if tg_id in ADMIN_ID and text == '/restart':
            subjects = get_subjects()
            u = {}
            print(f'u: {str(u)}\nsubjects: {str(subjects)}\n')
            print('Рестарт\n\n')

        # ожидаем номер ЭЖД и запрашиваем пароль
        if tg_id in u and u[tg_id]['route'] == 'f1_2': 
            f1_2(u, tg_id,text)
            if u[tg_id]['wait']:
                return 0
        
        # ожидаем пароль
        if tg_id in u and u[tg_id]['route'] == 'f1_3': 
            f1_3(u, tg_id,text)
            if u[tg_id]['wait']:
                return 0

        # начинаем с начала
        # поменяно местами f1_1 и f1_2 и f1_3 для возможности авторизации
        # далее все действия для авторизованных пользователей
        if (text == "/start" or (not tg_id in u) or get_login_authorization(tg_id) == None):
            u[tg_id] = {}
            f1_1(u, tg_id)
            if u[tg_id]['wait']:
                return 0

        # учительская. удаление ученика и деавторизация (без сброса результатов)
        if check_re_t(u[tg_id]['login']) and text.split(' ')[0] == '/reset_password':
            u_id = get_id_authorization(text.split(' ')[1])
            reset_password(text.split(' ')[1])
            if (u_id is not None) and (u_id in u): 
                del u[u_id]
            

        # учительская. результаты класса по выбранному предмету и теме
        if check_re_t(u[tg_id]['login']) and text.split(' ')[0] == '/result_class':
            result_class(u, tg_id, text.split(' ')[1])

        # учительская. добавление заданий
        if check_re_t(u[tg_id]['login']) and u[tg_id]['route'] == 'add_tasks':
            add_tasks(u, tg_id, text)
        
        # предлагаем список предметов
        if u[tg_id]['route'] == 'f2_1': 
            f2_1(u, tg_id)
            if u[tg_id]['wait']:
                return 0
      
        # ожидаем выбор предмета и запрашиваем тему
        if u[tg_id]['route'] == 'f2_2': 
            f2_2(u, tg_id, text)
            if u[tg_id]['wait']:
                return 0    
                
        # ожидаем тему
        if u[tg_id]['route'] == 'f2_3': 
            f2_3(u, tg_id,text)
            if u[tg_id]['wait']:
                return 0  

        # обучение по теме
        if u[tg_id]['route'] == 'f3_0': 
            f3_0(u, tg_id)
            if u[tg_id]['wait']:
                return 0
 
        # ожидаем ответа на задачу
        # поменяно местами f3_2 и f3_1 для циклического решения задач
        if u[tg_id]['route'] == 'f3_2': 
            f3_2(u, tg_id, text)
            if u[tg_id]['wait']:
                return 0 
 
        # предлагаем подходящую задачу
        if u[tg_id]['route'] == 'f3_1': 
            f3_1(u, tg_id)
            if u[tg_id]['wait']:
                return 0 

    except Exception as e:
        print('Ошибка:\n', traceback.format_exc())
        # для возврата к самому началу
        if tg_id in u: 
            del u[tg_id]
        msg = bot.send_message(tg_id,
                               f'{e}\noooops, попробуйте еще раз..\n\nВведите /start для продолжения')

# только документы
@bot.message_handler(content_types=['document'])
def router_doc(m):
    # пользователь
    tg_id = m.chat.id
    global u
    global subjects
    
    try:
        # документ
        doc = m.document
        
        # отладка
        if tg_id in u:
            print(u[tg_id], doc)
        else:
            print(tg_id, doc, "router_doc")

        # далее все действия для авторизованных пользователей
        if ((not tg_id in u) or get_login_authorization(tg_id) == None):
            u[tg_id] = {}
            f1_1(u, tg_id)
            if u[tg_id]['wait']:
                return 0

        # сохраняем инфо о последнем документе пользователя
        if tg_id in u:
            u[tg_id]['doc'] = doc
 
        # учительская. загрузка заданий
        if check_re_t(u[tg_id]['login']) and check_tasks(doc):
            promt_add_tasks(u, tg_id, doc)
            if u[tg_id]['wait']:
                return 0

    except Exception as e:
        print('Ошибка:\n', traceback.format_exc())
        # для возврата к самому началу
        if tg_id in u: 
            del u[tg_id]
        msg = bot.send_message(tg_id,
                               f'{e}\noooops, попробуйте загрузить документ еще раз..\n\nИли введите /start')



'''
def document_2(m):
    try:
        name = u[m.from_user.id]['doc_name']
        if(m.text == "1"):
            # определяем бд предмета
            subject = None
            for i in range(0,len(subjects)):
                if name.split('.')[0] == subjects[i]['name']:
                    subject = i
                    break
            
            if subject is None:
                os.remove(f"{PATH_TASKS}/{name}")
                raise Exception("Для создания нового предмета необходимо создать БД")
            
            
            insert_xlsx(subjects[subject]['path'],u[m.from_user.id]['doc_name'].split('.'), u[m.from_user.id]['doc'])
        else: 
            os.remove(f"{PATH_TASKS}/{name}")
    
    except Exception as e:
        print('Ошибка:\n', traceback.format_exc())
        msg = bot.send_message(m.chat.id,
                               f'{e}\n попробуем еще раз..\n\nВведите /start для продолжения')
'''
if __name__ == "__main__":
    start = time.time()
    print('start bot')
    bot.polling()
    print(time.time() - start)

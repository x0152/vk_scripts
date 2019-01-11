import vk_api
from datetime import datetime
import sys

help = '''
[name_script].py <login> <password> <countmsg>

   login - логин
   password - пароль
   countmsg - количество сообщений каждого чата (Максимум 200)
   Если countmsg равен нулю скрипт проверит возможность авторизации
'''

def auth_handler():
    key = input("Код двухфакторной аутентификации: ")
    remember_device = False 
    #remember_device = False

    return key, remember_device

def Auth(login, password):
    vk_session = vk_api.VkApi(login, password, auth_handler = auth_handler)

    try:
        vk_session.auth(token_only=True)
    except vk_api.AuthError as error_msg:
        print("Ошибка авторизации ({0})".format(error_msg))
        return False, vk_session

    print("Авторизация -> [OK]\n")
    return True, vk_session

def main():
   
    #handle arguments
    if len(sys.argv) != 4:
        print(help)
        exit(-1) 


    login = sys.argv[1]
    password = sys.argv[2]
    countmsg = int(sys.argv[3])

    countmsg = min([200, countmsg])
    countmsg = max([0, countmsg])
    
    #vk
    isAuth, vk_session = Auth(login, password)

    if countmsg == 0:
        exit(0) 

    values = {'offset': 0, 'count': 200, 'filter': "all"}
    response = vk_session.method('messages.getConversations', values)

    vk = vk_session.get_api()

    if len(response["items"]) == 0:
        print("Не удалось получить диалоги! (Возможно не правильный логин или пароль)")
        exit(-1)

    for chat in response["items"]:
        id = chat["conversation"]["peer"]["id"]
        msgs = vk_session.method('messages.getHistory', {'peer_id': id,'count': countmsg})

        user_info = vk.users.get(user_ids = id)
        if len(user_info) != 0:
            print("Чат с пользователем {0} {1} ({2}): ".format(user_info[0]["last_name"], user_info[0]["first_name"], id))
        else:
            print("Чат с пользователем {0}: ".format(id))
        

        for m in msgs["items"]:
            date = datetime.fromtimestamp(int(m["date"]))
            text = m["text"]
            if m["from_id"] == id:
                print("{0} Он: {1}".format(date, text))
            else:
                print("{0} Вы: {1}".format(date, text))

main()

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType 
from datetime import datetime
import sys

import pBotWrapper

help = '''
[name_script].py <login> <password> <countmsg>

   login - логин
   password - пароль

'''
def GetNameUser(vk, id):
    user_info = vk.users.get(user_ids = id)
    return "{0} {1}({2})".format(user_info[0]["last_name"], user_info[0]["first_name"], id)

def GetUnreadMessages(vk_session):

    unreadMsgs = {}
    values = {'offset': 0, 'count': 200, 'filter': "unread"}
    response = vk_session.method('messages.getConversations', values)

    vk = vk_session.get_api()

    if len(response["items"]) == 0:
        return unreadMsgs

    for chat in response["items"]:
        id = chat["conversation"]["peer"]["id"]
        msgs = vk_session.method('messages.getHistory', {'peer_id': id,'count': 1})

        items = msgs["items"]

        if len(items) == 0:
            lprint("Don't to get unread msg!") 
            continue
        
        date = datetime.fromtimestamp(int(items[0]["date"]))

        unreadMsgs[id] = {"text": items[0]["text"], "date": date}

        return unreadMsgs
        

def HandlerAnswer(msg):
    return msg.replace("pBot", "Андрюша").replace("7", "29")

def lprint(text):
    f.write(text + '\n')
    print(text)

def auth_handler():
    key = input("Код двухфакторной аутентификации: ")
    remember_device = True 

    return key, remember_device

def Auth(login, password):
    vk_session = vk_api.VkApi(login, password, auth_handler = auth_handler)

    try:
        vk_session.auth(token_only=True)
    except vk_api.AuthError as error_msg:
        lprint("Ошибка авторизации ({0})".format(error_msg))
        return False, vk_session

    lprint("Авторизация -> [OK]\n")
    return True, vk_session

def SendMessage(bot, vk, msg, user_id, user_name):

    answer = HandlerAnswer(bot.Ask(msg))

    if len(msg) <= 145:
        if len(answer) == 0:
            lprint("Bot не может ответить на этот вопрос -> {0}".format(user_name))
            return

        lprint("Bot -> {0}: {1}".format(user_name, answer))
        vk.messages.send(user_id = user_id, message = answer, random_id=0)
    else:
        lprint("Слишком большое сообщение ({0} символов) Bot не может на него ответить -> {1}".format(len(msg), user_name))

def main():
   
    #handle arguments
    if len(sys.argv) != 3:
        lprint(help)
        exit(-1) 

    login = sys.argv[1]
    password = sys.argv[2]

    #vk
    isAuth, vk_session = Auth(login, password)

    longpoll = VkLongPoll(vk_session)
    vk = vk_session.get_api()
    

    bots = {}

    unreadMsgs = GetUnreadMessages(vk_session)

    lprint("Все выведенное на экран будет записываться в файл log.txt. ")
        

    #Unreaded msgs 
    print("Непрочитанные сообщения {0}.".format(len(unreadMsgs)))
    for id, text in unreadMsgs.items():
        user_name = GetNameUser(vk, id)
        bot = pBotWrapper.pBot(user_name)

        if bot.Init() == False:
            lprint("Bot created error!") 
        bots[id] = bot

        lprint("{0}: Непрочитанное сообщение от {1}: {2}".format(text["date"], user_name, text["text"]))
        SendMessage(bot, vk, text["text"], id, user_name)

    lprint("Ожидание входящих сообщений...")

    #Input messages
    for event in longpoll.listen():
        
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            msg = event.text;
            answer = ""

            if msg == "":
                continue

            #athor message
            user_id = event.user_id
            user_name = GetNameUser(vk, user_id)

            lprint("{0}: Новое сообщение от {1}: {2}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_name, msg))
            
            bot = pBotWrapper.pBot(user_name)

            if user_id in bots: 
                bot = bots[user_id]
            else:
                if bot.Init() == False:
                    lprint("Bot created error!")
                    continue
                bots[user_id] = bot
                msg = "{0}: Инициализирован новый диалог с {1}: {2}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_name, msg)
                #vk.messages.send(user_id = 0, message = msg, random_id=0)
            
            SendMessage(bot, vk, msg, user_id, user_name)


f = open("log.txt", "a", buffering=1)

isRepeat = True;

while isRepeat:

    try:
        main()
    except vk_api.VkApiError as e:
        lprint(str(e))
        lprint("Restart...")
    except ConnectionError as e:
        lprint(str(e))
        lprint("Restart...")
    except Exception as e:

        if type(e).__name__ == "ReadTimeout":
            lprint(str(e))
            lprint("Restart...")
            continue

        lprint("TYPE:{0}; Text: {1}; Args: {2}.".format(type(e).__name__, str(e), e.args))
        lprint("Завершение...")
        f.close()
        isRepeat = False


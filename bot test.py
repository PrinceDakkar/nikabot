import telebot
import openai
import datetime
from collections import defaultdict
import random
import time
import pickle


def debounce(seconds=300):
    def decorate(func):
        last_call = [0.0]

        def wrapper(*args, **kwargs):
            elapsed = time.monotonic() - last_call[0]
            if elapsed > seconds:
                last_call[0] = time.monotonic()
                return func(*args, **kwargs)
            else:
                print(
                    f"Мы знаем, что вы умеете ждать: подождите еще {seconds - elapsed:.2f} секунд")
                return None

        return wrapper

    return decorate


@debounce(300)
def shiphip(message):
    try:
        shipUser1 = random.choice(list(users[message.chat.id].keys()))
        shipUser2 = random.choice(list(users[message.chat.id].keys()))
        while shipUser1 == shipUser2 and (users[message.chat.id][shipUser1][0] == None or users[message.chat.id][shipUser2][0] == None):
            shipUser1 = random.choice(list(users[message.chat.id].keys()))
            shipUser2 = random.choice(list(users[message.chat.id].keys()))
        lovetext = f"Напиши историю любви между @{users[message.chat.id][shipUser1][0]} и @{users[message.chat.id][shipUser2][0]}. Придумай как можно более интересную, интригующую и забавную историю. Доводи до абсурда и неожиданных концовок. По мере возможностей"

        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                                  messages=[
                                                      {"role": "system",
                                                       "content": "Yoy are copywriter."},
                                                      {"role": "user", "content": f"{lovetext}"}]
                                                  )
        bot.reply_to(
            message, f"❤️❤️\nЗашипперились @{users[message.chat.id][shipUser1][0]} и @{users[message.chat.id][shipUser2][0]}\n❤️❤️\nВот их история любви:\n {completion['choices'][0]['message']['content']}")
    except openai.error.RateLimitError:
        print("Rate limit reached, waiting ")
        time.sleep(30)
        return shiphip(message)


def generate_image(message):
    promptik = message.text[6:]
    response = openai.Image.create(
        prompt=promptik,
        n=1,
        size="512x512"
    )
    print(response)
    return response['data'][0]['url']


def generate_text(prompt):
    try:
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                                  messages=[
                                                      {"role": "user", "content": f"{prompt}"}]
                                                  )
        message = completion["choices"][0]["message"]["content"]
        return message
    except openai.error.RateLimitError:
        print("Rate limit reached, waiting ")
        time.sleep(10)
        return generate_text(prompt)


def generate_reply(prompt, message):
    try:
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                                  messages=[
                                                      {"role": "system",
                                                       "content": "You are the smart chat bot."},
                                                      {"role": "assistant",
                                                       "content": message.reply_to_message.text},
                                                      {"role": "user", "content": message.text}]
                                                  )
        message = completion["choices"][0]["message"]["content"]
        return message
    except openai.error.RateLimitError:
        print("Rate limit reached, waiting ")
        time.sleep(10)
        return generate_reply(prompt, message)


# model_engine = "text-davinci-003"
openai.api_key = "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"
bot = telebot.TeleBot('6292843670:AAESjXj9uCeazqD5opLkEZ4Ta4zk0gpuuDc')
word = "ника"
bot_id = bot.get_me().id
chat_names = []


def load_users():
    try:
        with open('users.pickle', 'rb') as f:
            return pickle.load(f)
    except IOError:
        # If file doesn't exist, return empty defaultdict
        return defaultdict(dict)

# Function to save users to file


def save_users(users):
    with open('users.pickle', 'wb') as f:
        pickle.dump(users, f)


# Load users from file
users = load_users()
conversations = {}
message_num = 0


def store_message(message):
    global message_num
    if message.chat.id not in conversations:
        # Создаем новый чат
        conversations[message.chat.id] = {}
    if len(conversations[message.chat.id]) > 100:
        keys = list(conversations[message.chat.id].keys())
        del conversations[message.chat.id][keys[0]]

    if message.from_user.username == None:
        if message.from_user.first_name != None:
            new_message = {'sender': message.from_user.first_name,
                           'message': message.text}
        else:
            new_message = {'sender': message.from_user.last_name,
                           'message': message.text}
    else:

        new_message = {'sender': message.from_user.username,
                       'message': message.text}
    message_num += 1
    conversations[message.chat.id][message_num] = new_message
    # добавляем элемент в словарь


def generate_summarize(message):
    prompt = ""
    print(f"summarizing {len(conversations[message.chat.id])} messages")
    length = len(conversations[message.chat.id])

    if length < 10:
        return "В чате слишком мало новых сообщений"

    for mes in conversations[message.chat.id].values():
        prompt += (str(mes['sender']) + ": " + mes['message'] + "\n")

    try:
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                                  messages=[
                                                        {"role": "system",
                                                         "content": "You are copywriter"},
                                                        {"role": "user", "content": f"Напишите подробную историю общения в чате. Дайте полное описание контекста обсуждения.Укажите имена участников общения. Объясните, какая информация была получена в результате обсуждения в чате и как это повлияло на развитие беседы. используй вольный стиль общений. Пиши на русском языке:\n {prompt}"}]
                                                  )
        answer = completion["choices"][0]["message"]["content"]
        print(completion['usage'])

        return answer

    except openai.error.RateLimitError:
        print("Rate limit reached, waiting ")
        time.sleep(10)
        return generate_summarize(message)


@bot.message_handler(commands=['chats'])
def check(message):
    for value in chat_names:
        text_value = '; '.join(str(v) for v in chat_names)
    bot.send_message(
        message.chat.id, text_value)


@bot.message_handler(commands=['callpeople'])
def callall(message):
    user_status = bot.get_chat_member(
        message.chat.id, message.from_user.id).status
    if (message.chat.type == "supergroup" or message.chat.type == "group") and (user_status == 'creator' or user_status == 'administrator'):
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                                  messages=[
                                                      {"role": "system",
                                                          "content": "You are copywriter"},
                                                      {"role": "user", "content": "Напиши пригласительное письмо для игры в мафию. Ты должен обратиться ко всем участникам группового чата. Используй деловой стиль речи и юмор."}]
                                                  )
        bot.reply_to(message, completion["choices"][0]["message"]["content"])
        keys = list(users[message.chat.id].keys())
        callmessage = ""
        count = 0
        for i in range(0, len(keys)):
            id = keys[i]
            if users[message.chat.id][id][0] == None:
                callmessage = callmessage + \
                    f'<a href="tg://user?id={id}">{users[message.chat.id][id][1]}</a>, '
                count += 1
            else:
                callmessage = callmessage + "@" + \
                    users[message.chat.id][id][0] + ", "
                count += 1
            if count == 5:
                bot.send_message(message.chat.id, callmessage,
                                 parse_mode="HTML")
                callmessage = ""
                count = 0
            if i == len(keys) - 1:
                bot.send_message(message.chat.id, callmessage,
                                 parse_mode="HTML")
        bot.send_message(message.chat.id, completion.choices[0].text)
    else:
        bot.send_message(
            message.chat.id, "Вы не являетесь администратором, чтобы пользоваться этой командой")


@bot.message_handler(commands=['start'])
def start_message(message):
    if message.chat.type == "private":
        bot.send_message(message.chat.id, "Привет ✌️\nЯ умный бот. Чтобы я ответил на любой твой вопрос напиши в нем мое имя. Например:\nНика напиши рецепт вкусного блюда.\nБот может. Это зависит от длины сообщения, которое он сгенерирует.")


@bot.message_handler(commands=['summarize'])
def summarize_message(message):
    bot.reply_to(
        message, f"Отчет за {len(conversations[message.chat.id])} сообщений: \n {generate_summarize(message)} ")
    conversations[message.chat.id] = {}


@bot.message_handler(commands=['privatesummarize'])
def private_summarize_message(message):
    bot.send_message(message.from_user.id,
                     f"Отчет за {len(conversations[message.chat.id])} сообщений: \n {generate_summarize(message)}")


@bot.message_handler(content_types=['text'])
def reply_to_message(message):
    store_message(message)
    if message.chat.title not in chat_names:
        chat_names.append(message.chat.title)

    promptik = message.text[4:]
    timestamp = message.date
    if message.chat.id not in users.keys():
        users[message.chat.id] = {}
    else:
        users[message.chat.id][message.from_user.id] = [
            message.from_user.username, message.from_user.first_name]

    date = datetime.datetime.fromtimestamp(timestamp)
    if message.chat.title == None:
        bot.send_message(
            349883265, f"[{date}].\nUser: @{message.from_user.username} {message.from_user.first_name} {message.from_user.last_name}")
    if message.reply_to_message != None:
        if message.reply_to_message.from_user.id == bot_id:

            # completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",
            #                                           messages=[
            #                                               {"role": "system",
            #                                                "content": "You are the smart chat bot."},
            #                                               {"role": "assistant",
            #                                                "content": message.reply_to_message.text},
            #                                               {"role": "user", "content": message.text}]
            #                                           )
            answer = generate_reply(promptik, message)
            bot.reply_to(
                message, answer)
    elif word == message.text[:4].lower() and message.text.lower() != word:
        # completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",
        #                                           messages=[
        #                                               {"role": "user", "content": f"{promptik}"}]
        #                                           )
        answer = generate_text(promptik)
        bot.reply_to(message, answer)
    elif (message.chat.type == 'group' or 'supergroup') and "шипшип" in message.text.lower():
        shiphip(message)
    elif ("генерь" == message.text[:6].lower()):
        url = generate_image(message)
        bot.send_photo(message.chat.id, url, message.text[6:])

    save_users(users)


while True:
    try:
        bot.polling(none_stop=True, interval=0)

    except Exception as e:
        print(e)  # или просто print(e) если у вас логгера нет,
        # или import traceback; traceback.print_exc() для печати полной инфы
        time.sleep(15)

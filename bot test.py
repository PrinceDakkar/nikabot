import telebot
from dotenv import load_dotenv
import openai
import os
import datetime
from collections import defaultdict
import random
import time


load_dotenv()


openai.api_key = os.getenv('OPENAI_TOKEN')
bot = telebot.TeleBot(os.getenv('TELEGRAM_TOKEN'))
word = "ника"
bot_id = bot.get_me().id


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


@bot.message_handler(commands=['start'])
def start_message(message):
    if message.chat.type == "private":
        bot.send_message(
            message.chat.id, "Привет ✌️\nЯ умный бот. Я отвечу на любой твой вопрос. Например:\nНапиши рецепт вкусного блюда.")


print("Bot running")


@bot.message_handler(content_types=['text'])
def reply_to_message(message):
    print(message)

    promptik = message.text[4:]
    timestamp = message.date

    date = datetime.datetime.fromtimestamp(timestamp)

    if message.chat.type == "private":
        bot.send_message(
            349883265, f"[{date}].\nUser: @{message.from_user.username} {message.from_user.first_name} {message.from_user.last_name}")

        if ("генерь" == message.text[:6].lower()):
            url = generate_image(message)
            bot.send_photo(message.chat.id, url, message.text[6:])
        if message.reply_to_message != None:
            answer = generate_reply(promptik, message)
            bot.reply_to(
                message, answer)
        else:
            answer = generate_text(message.text)
            bot.reply_to(
                message, answer)
    else:
        if ("генерь" == message.text[:6].lower()):
            url = generate_image(message)
            bot.send_photo(message.chat.id, url, message.text[6:])
        if message.reply_to_message != None and message.reply_to_message.from_user.id == bot_id:
            answer = generate_reply(promptik, message)
            bot.reply_to(
                message, answer)
        elif word == message.text[:4].lower() and message.text.lower() != word:
            answer = generate_text(promptik)
            bot.reply_to(message, answer)


while True:
    try:
        bot.polling(none_stop=True, interval=0)

    except Exception as e:
        print(e)  # или просто print(e) если у вас логгера нет,
        # или import traceback; traceback.print_exc() для печати полной инфы
        time.sleep(15)

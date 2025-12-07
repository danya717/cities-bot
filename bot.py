import geonamescache
import telebot
import geonamescache
import time
import wikipedia
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')

gc = geonamescache.GeonamesCache()
bot = telebot.TeleBot(TOKEN)

all_cities = gc.get_cities()
cities = []
score = 0

def find_city(letter):
    letter = letter.upper()
    for i in all_cities:
        names = all_cities[i].get("alternatenames")
        for name in names:
            if name:
                if name in cities:
                    break
                if name[0] == letter:
                    lat = all_cities[i].get('latitude')
                    lon = all_cities[i].get('longitude')
                    return name, lat, lon
        # return None, 0, 0

def get_last_letter():
    if cities:
        last_city = cities[-1]
        last_letter = last_city[-1]
        if last_letter == 'ь' or last_letter == 'ъ':
            last_letter = last_city[-2]
        last_letter = last_letter.upper()
        return last_letter

def get_info(city):
    wikipedia.set_lang('ru')
    answers = wikipedia.search(city)
    if answers:
        info_text = wikipedia.summary(answers[0], sentences=5)
        return info_text
    else:
        return f'Информация о {city} не найдена'


@bot.message_handler(commands=['start'])
def start(message):
    global score
    score = 0
    cities.clear()
    bot.send_message(message.chat.id, "Игра запущена! Назови город первым")

@bot.message_handler(commands=['stop'])
def stop(message):
    global score
    score = 0
    cities.clear()
    bot.send_message(message.chat.id, 'Игра остановлена')

@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(
        message.chat.id,
        'Список доступных комманд:\n/start - Запустить игру\n/stop - Остановить игру'
    )

@bot.message_handler(content_types=['text'])
def message_handler(message):
    global score
    city = message.text
    bot_last_letter = get_last_letter()
    if city[0] != bot_last_letter and bot_last_letter is not None:
        bot.send_message(message.chat.id, f'Город должен начинаться с буквы <b>{bot_last_letter}</b>', parse_mode='HTML')
    if city in cities:
        bot.send_message(message.chat.id, 'Этот город уже был назван')
        return
    user_cities = gc.search_cities(city)
    if not user_cities:
        bot.send_message(message.chat.id, 'К сожалению, такого города нету')
        return
    cities.append(city)
    score += 1
    bot.send_message(message.chat.id, f'👌Отлично! Такой город существует. Ваш счет: {score}')
    lat = user_cities[0].get('latitude')
    lon = user_cities[0].get('longitude')
    bot.send_location(message.chat.id, lat, lon)
    bot.send_message(message.chat.id, get_info(city), parse_mode='HTML')
    time.sleep(2)


    letter = get_last_letter()


    bot.send_message(
        message.chat.id,
        f'Я должен сказать город на букву <b>{letter}</b>',
        parse_mode='HTML'
    )
    bot_city, lat, lon = find_city(letter)
    cities.append(bot_city)
    bot.send_message(message.chat.id, f'<b>{bot_city}</b>', parse_mode='HTML')
    bot.send_location(message.chat.id, lat, lon)
    bot.send_message(message.chat.id, get_info(bot_city), parse_mode='HTML')
    bot_last_letter = get_last_letter()
    bot.send_message(
        message.chat.id,
        f'Твоя очередь! Назови город на букву: <b>{bot_last_letter}</b>',
        parse_mode='HTML'
    )



bot.polling(non_stop=True)
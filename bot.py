import geonamescache
import random
import telebot
import geonamescache
import time
import wikipedia
import os
from dotenv import load_dotenv
import requests
import json
import os.path

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
API_KEY = os.getenv('API_KEY')

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
    try:
        wikipedia.set_lang('ru')
        answers = wikipedia.search(city)
        if answers:
            info_text = wikipedia.summary(answers[0], sentences=5)
            return info_text
        else:
            return f'Информация о {city} не найдена'
    except (wikipedia.DisambiguationError,
            wikipedia.HTTPTimeoutError,
            wikipedia.PageError,
            wikipedia.RedirectError,
            wikipedia.WikipediaException):
        return f'Возникла ошибка при попытке получить информацию о городе {city}'

def get_img(city):
    try:
        wikipedia.set_lang('ru')
        answers = wikipedia.search(city)
        if not answers:
            return None
        page = wikipedia.page(answers[0])
        images = []
        for img in page.images:
            file_ext = os.path.splitext(img)[1]
            file_ext = file_ext.lower()
            if file_ext == '.png' or file_ext == '.jpg' or file_ext == '.jpeg':
                images.append(img)
            if images:
                random_img = random.choice(images)
                return random_img
            else:
                return None
    except (wikipedia.DisambiguationError,
            wikipedia.HTTPTimeoutError,
            wikipedia.PageError,
            wikipedia.RedirectError,
            wikipedia.WikipediaException):
        return None

def send_city_img(city, id):
    image_url = get_img(city)
    try:
        if image_url:
            bot.send_photo(id, image_url, parse_mode='HTML')
        else:
            bot.send_message(id, f'Картинка с городом {city} не найдена')
    except Exception as e:
        bot.send_message(id, f'Картинка с городом {city} не найдена')
        print(f'При отправки картинки {image_url} Было вызвано исключение {e}')

def send_city_weather(city, id, lat, lon):
    try:
        response = requests.get(
            f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=ru')
        data = json.loads(response.text)
        weather = data.get('weather')[0].get('description')
        main = data.get('main')
        temp = main.get('temp')
        feels_like = main.get('feels_like')
        pressure = main.get('pressure')
        humidity = main.get('humidity')
        img_code = data.get('weather')[0].get('icon')
        img_url = f'https://openweathermap.org/img/wn/{img_code}@2x.png'
        text = (f"<b>{city}</b>\nПогода в городе {city}: : <b>{weather}</b>\n🌡Температура воздуха: <b>{temp}°C</b>,"
                f" ощущается как <b>{feels_like}°C</b>\n☁️ Атмосферное давление: <b>{pressure}</b>"
                f"\n💧 Влажность воздуха: <b>{humidity}%</b>")
        bot.send_photo(id, photo=img_url, caption=text, parse_mode='HTML')
    except Exception as e:
        bot.send_message(id, f"Прогноз погоды для города {city} не найден")
        print(f'При отправки погоды для {city} вызвано исключение {e}')




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
    try:
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
        send_city_img(city, message.chat.id)
        send_city_weather(city, message.chat.id, lat, lon)


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
        send_city_img(bot_city, message.chat.id)
        send_city_weather(bot_city, message.chat.id, lat, lon)
        bot.send_message(
            message.chat.id,
            f'Твоя очередь! Назови город на букву: <b>{bot_last_letter}</b>',
            parse_mode='HTML'
        )
    except wikipedia.exceptions.PageError:
        bot.send_message(messsage.chat.id, "Такой город не найден")





bot.polling(non_stop=True)
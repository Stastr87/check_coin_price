
import time
import logging
import telebot
from telebot import types
import coin_module
import tools_module
import sys
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s_%(levelname)s: %(message)s')

#Перенести в другой модуль
def retry(func):  # Декоратор функции в котором выполняется бесконечный цикл запросов
    def wrappedFunc(*args, **kwargs):
        while True:
            logging.debug(f'wrappedFunc: {func.__name__}() called')
            func(*args, **kwargs)
            time.sleep(1)
    return wrappedFunc

#Перенести в другой модуль
@retry
def update_coin_list(m):  # Обновление котировок в списке объектов Coin_obj
    response_data, response_code = coin_module.check_quotes()
    actual_quotes = coin_module.coin_filter(response_data, response_code)

    # Создать новый список с данными для обработки
    coin_list = coin_module.create_new_coin_list(actual_quotes)

    for coin in coin_list:  # Зафиксировать цену вначале таймфрейма
        coin['price_A'], coin['timestamp_A'] = coin_module.check_price(
            actual_quotes, coin['coin_name'])

    # Время ожидания до следующей итерации
    time.sleep(int(tools_module.get_config()['time_frame']))

    # Получить свежие котировки
    response_data, response_code = coin_module.check_quotes()
    actual_quotes = coin_module.coin_filter(response_data, response_code)

    # Для проверки того что в новых котировках имеется тикер для сравнения
    actual_quotes_tikers = []
    for quote in actual_quotes:
        actual_quotes_tikers.append(quote["symbol"])

    for coin in coin_list:  # Зафиксировать цену вконце таймфрейма
        # Проверка на наличие в котировках тикер для сравнения
        if coin['coin_name'] in actual_quotes_tikers:
            coin['price_B'], coin['timestamp_B'] = coin_module.check_price(
                actual_quotes, coin['coin_name'])
    tools_module.save_data(coin_list, 'output_data.json')

    coin_list = coin_module.calculate_price_moving(coin_list)
    # Подсчитать разницу и сохранить файл
    tools_module.save_data(coin_list, 'calculated_output_data.json')
    logging.debug(f'update_coin_list: OK. Coin list updated!')

    alert_list = []
    for item in coin_list:
        if abs(item["price_moving"]) > float(tools_module.get_config()["alert_threshold"]):
            alert_list.append(item)
            position = None
            if item["price_moving"] > 0:
                position = "long"
            else:
                position = "short"

            message_string = f'{item["coin_name"]} {position}, price moving {round(item["price_moving"],2)}%'
            bot.send_message(m.chat.id, message_string)
    if alert_list == []:
        pass
        #bot.send_message(m.chat.id, 'Сигналов нет.')
    tools_module.save_data(alert_list, 'alert_list.json')
    logging.debug(f'update_coin_list: OK. alert_list updated!')
    return alert_list


#Реализация бота
bot = telebot.TeleBot(tools_module.get_token()["something_unimportant"])


#Добавить команду /stop

@bot.message_handler(commands=["start"])
def start(m, res=False):
    bot.send_message(
        m.chat.id, 'Бот который ослеживает котировки согласно настройкам')
    # Добавляем две кнопки
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("/start_check_quotes")
    item2 = types.KeyboardButton("/change_config")
    markup.add(item1)
    markup.add(item2)
    bot.send_message(m.chat.id, 'Make your choice', reply_markup=markup)




@bot.message_handler(content_types=["text"])
def check_quotes(m, res=False):
    # Тут нужно описание что делает бот
    if m.text.strip()=='/start_check_quotes':
        bot.send_message(m.chat.id, 'Бот начал отслеживать котировки')
        update_coin_list(m)
        tools_module.kill_bot()
    elif  m.text.strip()=="/change_config":   #реализовать изменение конфига
        pass


##------исполняемый код скрипта-------
# Запускаем бота

bot.polling(none_stop=True, interval=0)

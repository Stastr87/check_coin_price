import requests
import json
import time
import logging
import os
import math
import tools_module
from pprint import pprint
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s_%(levelname)s: %(message)s')


class Coin_obj(object):
    def __init__(self, coin_name=None,price_A=None,timestamp_A=None,price_B=None,timestamp_B=None):
        self.coin_name=coin_name
        self.price_A=price_A
        self.timestamp_A=timestamp_A
        self.price_B=price_B
        self.timestamp_B=timestamp_B
        self.price_moving=None

    def get_price_moving(price_A, price_B):
        if price_A!=None and price_B!=None:
            price_moving=(100*(float(price_B)-float(price_A)))/float(price_A)
        else:
            price_moving=0
        return price_moving

    def to_json(self):
        data={}
        data['coin_name']=self.coin_name
        data['price_A']=self.price_A
        data['timestamp_A']=self.timestamp_A
        data['price_B']=self.price_B
        data['timestamp_B']=self.timestamp_B
        data['price_moving']=self.price_moving
        return data

def check_quotes():    #Функция запроса котировок
    method='/fapi/v1/ticker/price'
    headers = {'Content-type': 'application/json',
               'Content-Encoding': 'utf-8'}
    host=tools_module.get_config()["host"]
    logging.debug(f'{__name__}.check_quotes(): host={host}')
    try:
        response=requests.get(f'{host}{method}', headers=headers)
        logging.debug(f'{__name__}.check_quotes() response.url={response.url}')
        response_data, response_code=response.json(), response.status_code
    except:
        logging.debug(f'{__name__}.check_quotes() error to get response.url')
        response_data, response_code='Connection_error', None
    return response_data, response_code

def coin_filter(quotes,response_code):    #Фильтр тикеров согласно настройкам в конфиге
    if response_code==200:
       try:
           for item in quotes:
               if item['symbol'][-1:] != tools_module.get_config()['coin_mask']:    #Удалить монеты в которых последний символ не соответсвует маске
                   quotes.remove(item)
               if item['symbol'] in tools_module.get_config()['waste_coin_list']:    #Удалить из списка определенные монеты
                   quotes.remove(item)
           tools_module.save_data(quotes, 'response_data.json')    # Сохраняются данные с примененым фильтром 
           logging.debug(f'{__name__}.coin_filter(): OK')
       except:
           tools_module.save_data(quotes,'response_data.json')
           logging.debug(f'{__name__}.coin_filter(): NO NEED')
    else:
        logging.debug(f'{__name__}.coin_filter(): FAIL to get response from server, response_code: {response_code}')
    return quotes

def create_new_coin_list(some_coin_list):    #Создает список из новых объектов JSON
    new_coin_list=[]
    for item in some_coin_list:
        new_coin_list.append(Coin_obj(item['symbol'], item['price'],item['time']).to_json())
    return new_coin_list

def check_price(quotes_json_data, coin):    #Возвращает цену и таймштамп переданного тикера
    for item in quotes_json_data:
        if item['symbol']==coin:
            price=item['price']
            time_stmp=item['time']

    return price, time_stmp

def calculate_price_moving(some_coin_list):    #Вносит изменения в список объектов Coin_obj 
    for item in some_coin_list:
        item['price_moving']=Coin_obj.get_price_moving(item['price_A'],item['price_B'])
    return some_coin_list


def retry(func):  # Декоратор функции в котором выполняется бесконечный цикл запросов
    def wrappedFunc(*args, **kwargs):
        while True:
            logging.debug(f'wrappedFunc: {func.__name__}() called')
            func(*args, **kwargs)
            time.sleep(1)
    return wrappedFunc


@retry
def update_coin_list(m, bot):  # Обновление котировок в списке объектов Coin_obj
    response_data, response_code = check_quotes()
    actual_quotes = coin_filter(response_data, response_code)

    # Создать новый список с данными для обработки
    coin_list = create_new_coin_list(actual_quotes)

    for coin in coin_list:  # Зафиксировать цену вначале таймфрейма
        coin['price_A'], coin['timestamp_A'] = check_price(
            actual_quotes, coin['coin_name'])

    # Время ожидания до следующей итерации
    time.sleep(int(tools_module.get_config()['time_frame']))

    # Получить свежие котировки
    response_data, response_code = check_quotes()
    actual_quotes = coin_filter(response_data, response_code)

    # Для проверки того что в новых котировках имеется тикер для сравнения
    actual_quotes_tikers = []
    for quote in actual_quotes:
        actual_quotes_tikers.append(quote["symbol"])

    for coin in coin_list:  # Зафиксировать цену вконце таймфрейма
        # Проверка на наличие в котировках тикер для сравнения
        if coin['coin_name'] in actual_quotes_tikers:
            coin['price_B'], coin['timestamp_B'] = check_price(
                actual_quotes, coin['coin_name'])
    tools_module.save_data(coin_list, 'output_data.json')

    coin_list = calculate_price_moving(coin_list)
    # Подсчитать разницу и сохранить файл
    tools_module.save_data(coin_list, 'calculated_output_data.json')
    logging.debug(f'update_coin_list: OK. Coin list updated!')

    alert_list = []
    for item in coin_list:
        if abs(item["price_moving"]) > float(tools_module.get_config()["alert_threshold"]):
            alert_list.append(item)
            position = None
            if item["price_moving"] > 0:
                position = "*LONG*"
            else:
                position = "*SHORT*"
            current_price=round(float(item["price_B"]),5)
            price_moving=round(float(item["price_moving"]),2)
            message_string = f'*{item["coin_name"]}* = {current_price} ({price_moving}%), {position}'
            bot.send_message(m.chat.id, message_string, parse_mode = "Markdown")
    if alert_list == []:
        pass

    tools_module.save_data(alert_list, 'alert_list.json')
    logging.debug(f'update_coin_list: OK. alert_list updated!')
    return alert_list
import requests
import json
import time
import logging
import os
import math
from pprint import pprint

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s_%(levelname)s: %(message)s')
# Добавить методы подключения телеграм-бота
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

def get_config():
    with open('config.json', 'r') as config_file:
        config=json.loads(config_file.read())
        config_file.close()
        return config

def retry(func):    #Декоратор функции в котором выполняется бесконечный цикл запросов
    def wrappedFunc(*args, **kwargs):
        while True:
            logging.debug(f'wrappedFunc: {func.__name__}() called')
            func(*args, **kwargs)
            time.sleep(1)
    return wrappedFunc

def check_quotes():    #Функция запроса котировок
    method='/fapi/v1/ticker/price'
    headers = {'Content-type': 'application/json',
               'Content-Encoding': 'utf-8'}
    try:
        response=requests.get(f'{host}{method}', headers=headers)
        response_data, response_code=response.json(), response.status_code
    except:
        response_data, response_code='Connection_error', None
    return response_data, response_code

def save_data(json_data, file_name):    #Сохранение данных json в файл
    if not os.path.exists('temp'): os.makedirs('temp') 
    with open(os.path.join('.','temp',file_name), 'w') as response_data_file:
        response_data_file.write(json.dumps(json_data, indent=4, sort_keys=True))
        response_data_file.close()

def coin_filter(quotes,response_code):
    if response_code==200:
       try:
           for item in quotes:
               if item['symbol'] in get_config()['waste_coin_list']:    #Удалить из списка определенные монеты
                   quotes.remove(item)
               if item['symbol'][-4:] in get_config()['coin_mask']:    #Удалить из списка монеты по заданной маске
                   quotes.remove(item)
           save_data(quotes, 'response_data.json')    # Сохраняются данные с примененым фильтром 
           logging.debug(f'coin_filter: OK')
       except:
           save_data(quotes,'response_data.json')
           logging.debug(f'coin_filter: NO NEED')
    else:
        logging.debug(f'coin_filter: FAIL to get response from server, response_code: {response_code}')
    return quotes

def create_new_coin_list(some_coin_list):
    new_coin_list=[]
    for item in some_coin_list:
        new_coin_list.append(Coin_obj(item['symbol'], item['price'],item['time']).to_json())
    return new_coin_list

def check_price(quotes_json_data, coin):
    for item in quotes_json_data:
        if item['symbol']==coin:
            price=item['price']
            time_stmp=item['time']

    return price, time_stmp

def calculate_price_moving(some_coin_list):
    for item in some_coin_list:
        item['price_moving']=Coin_obj.get_price_moving(item['price_A'],item['price_B'])
    return some_coin_list

@retry
def update_coin_list():
    response_data, response_code=check_quotes()
    actual_quotes=coin_filter(response_data, response_code)

    coin_list=create_new_coin_list(actual_quotes)     #Создать новый список с данными для обработки

    for coin in coin_list:    #Зафиксировать цену вначале таймфрейма
        coin['price_A'], coin['timestamp_A']=check_price(actual_quotes, coin['coin_name'])

    
    time.sleep(int(get_config()['time_frame']))    #Время ожидания до следующей итерации

    response_data, response_code=check_quotes()    # Получить свежие котировки
    actual_quotes=coin_filter(response_data, response_code)

    actual_quotes_tikers=[]    #Для проверки того что в новых котировках имеется тикер для сравнения
    for quote in actual_quotes:
        actual_quotes_tikers.append(quote["symbol"])

    for coin in coin_list:    #Зафиксировать цену вконце таймфрейма
        if coin['coin_name'] in actual_quotes_tikers:    #Проверка на наличие в котировках тикер для сравнения
            coin['price_B'], coin['timestamp_B']=check_price(actual_quotes, coin['coin_name'])
    save_data(coin_list,'output_data.json')
    
    coin_list=calculate_price_moving(coin_list)
    save_data(coin_list,'calculated_output_data.json')    #Подсчитать разницу и сохранить файл
    logging.debug(f'update_coin_list: OK. Coin list updated!')
    
    alert_list=[]
    for item in coin_list:
        if abs(item["price_moving"])>float(get_config()["alert_threshold"]):
            alert_list.append(item)
        
    save_data(alert_list,'alert_list.json')
    logging.debug(f'update_coin_list: OK. alert_list updated!')

##------исполняемый код скрипта-------

host=get_config()["host"]
update_coin_list()
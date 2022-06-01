import requests
import json
import time
import logging
import os
from pprint import pprint

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s_%(levelname)s: %(message)s')

#Есть
class Coin_obj(object):
    def __init__(self, coin_name=None,price_A=None,timestamp_A=None,price_B=None,timestamp_B=None):
        self.coin_name=coin_name
        self.price_A=price_A
        self.timestamp_A=timestamp_A
        self.price_B=price_B
        self.timestamp_B=timestamp_B
        self.price_moving=None

    def get_price_moving(price_A, price_B):
        price_moving=(float(price_A)-float(price_B))/float(price_B)
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

#Есть
def get_config():
    with open('config.json', 'r') as config_file:
        config=json.loads(config_file.read())
        config_file.close()
        return config

#Есть
def get_quotes_data():
    with open(os.path.join('.','temp','response_data.json'), 'r') as quotes_file:
        quotes=json.loads(quotes_file.read())
        quotes_file.close()
    return quotes
#Не требуется
def save_data(json_data):    #Сохранение данных json в файл
    with open(os.path.join('.','temp','output_data.json'), 'w', encoding='utf-8') as output_data_file:
        output_data_file.write(json.dumps(json_data, indent=4, sort_keys=True))
        output_data_file.close()

#Есть
def create_new_coin_list(quotes_list):
    coin_list=[]
    for item in quotes_list:
        coin_list.append(Coin_obj(item['symbol'], item['price'],item['time']).to_json())
    return coin_list
# Есть
def calculate_price_moving(some_coin_list):
    for item in some_coin_list:
        item['price_moving']=Coin_obj.get_price_moving(item['price_A'],item['price_B'])
    return some_coin_list
# Есть
def check_price(quotes_json_data, coin):
    for item in quotes_json_data:
        if item['symbol']==coin:
            price=item['price']
            time_stmp=item['time']
    return price, time_stmp
# Есть
def retry(func):    #Декоратор функции в котором выполняется бесконечный цикл запросов
    def wrappedFunc(*args, **kwargs):
        while True:
            logging.debug(f'{func.__name__}() called')
            func(*args, **kwargs)
            time.sleep(1)
    return wrappedFunc

@retry
def update_coin_list():
    config=get_config()    #Подгрузить актуальные настройки
    quotes_list=get_quotes_data()    #Получить исходные данные
    coin_list=create_new_coin_list(quotes_list)     #Создать новый список с данными для обработки

    for coin in coin_list:    #Зафиксировать цену вначале таймфрейма
        coin['price_A'], coin['timestamp_A']=check_price(quotes_list, coin['coin_name'])
    
    time.sleep(int(config['time_frame']))    #Время ожидания до следующей итерации
    quotes=get_quotes_data()    # Получить свежие котировки
    
    for coin in coin_list:    #Зафиксировать цену вконце таймфрейма
        coin['price_B'], coin['timestamp_B']=check_price(quotes, coin['coin_name'])

    save_data(calculate_price_moving(coin_list))    #Подсчитать разницу и сохранить файл
    logging.debug(f'Coin list updated!')

##--------------Основной код---------------

update_coin_list()





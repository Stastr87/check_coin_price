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
               if item['symbol'] in tools_module.get_config()['waste_coin_list']:    #Удалить из списка определенные монеты
                   quotes.remove(item)
               if item['symbol'][-4:] in tools_module.get_config()['coin_mask']:    #Удалить из списка монеты по заданной маске
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

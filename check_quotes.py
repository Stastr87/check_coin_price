import requests
import json
import time
import logging
from pprint import pprint

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s_%(levelname)s: %(message)s')

def get_config():
    with open('config.json', 'r') as config_file:
        config=json.loads(config_file.read())
        config_file.close()
        return config
config=get_config()
host=config["host"]


def retry(func):    #Декоратор функции в котором выполняется бесконечный цикл запросов
    def wrappedFunc(self, *args, **kwargs):
        while True:
            logging.debug(f'{func.__name__}() called')
            func(self, *args, **kwargs)
            time.sleep(59)
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

def open_quotes_file():
    with open('quotes.json', 'r', encoding='utf-8') as quotes_file:
        quotes=json.loads(quotes_file.read())
        quotes_file.close()
    return quotes

def save_data(json_data):    #Сохранение данных json в файл
    with open('response_data.json', 'w') as response_data_file:
        response_data_file.write(json.dumps(json_data, indent=4, sort_keys=True))
        response_data_file.close()

@retry
def update_coin_list(*data, coin_list={}):
    result_data=data[0]
    quotes=result_data[0]    #парсинг запроса 
    #quotes=result_data     #debug string
    response_code=result_data[1]
    #response_code=200    # DEBUG string
    if response_code==200:
       try:
           for item in quotes:
               if item['symbol'] in config['waste_coin_list']:    #Удалить из списка определенные монеты
                   quotes.remove(item)
               if item['symbol'][-4:] in config['coin_mask']:    #Удалить из списка монеты по заданной маске
                   quotes.remove(item)
           save_data(quotes)    # Сохраняются данные с примененым фильтром 
           logging.debug(f'Данные обновлены')
       except:
           save_data(quotes)
           logging.debug(f'Ошибка фильтрации, но данные обновлены')
    else:
        logging.debug(f'Ошибка получения данных от сервера, response_code: {response_code}')


update_coin_list(check_quotes())
import requests
import json
import time
import logging
from pprint import pprint

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s_%(levelname)s: %(message)s')
class Coin_obj(object):
    def __init__(self, coin_name=None,price_A=None,timestamp_A=None,price_B=None,timestamp_B=None):
        self.coin_name=coin_name
        self.price_A=price_A
        self.timestamp_A=timestamp_A
        self.price_B=price_B
        self.timestamp_B=timestamp_B

    def to_json(self):
        data={}
        data['coin_name']=self.coin_name
        data['price_A']=self.price_A
        data['timestamp_A']=self.timestamp_A
        data['price_B']=self.price_B
        data['timestamp_B']=self.timestamp_B
        return data


def get_config():
    with open('config.json', 'r') as config_file:
        config=json.loads(config_file.read())
        config_file.close()
        return config


def get_quotes_data():
    with open('response_data.json', 'r') as quotes_file:
        quotes=json.loads(quotes_file.read())
        quotes_file.close()
    return quotes

def save_data(json_data):    #Сохранение данных json в файл
    with open('output_data.json', 'w', encoding='utf-8') as output_data_file:
        output_data_file.write(json.dumps(json_data, indent=4, sort_keys=True))
        output_data_file.close()


def create_new_coin_list(quotes_list):
    coin_list=[]
    for item in quotes_list:
        coin_list.append(Coin_obj(item['symbol'], item['price'],item['time']).to_json())
    return coin_list

def check_price(quotes_json_data, coin):
    
    for item in quotes_json_data:
        if item['symbol']==coin:
            price=item['price']
            time_stmp=item['time']
    return price, time_stmp


##--------------Основной код---------------
config=get_config()

quotes_list=get_quotes_data()

coin_list=create_new_coin_list(quotes_list)


for coin in coin_list:
    price, time_stmp=check_price(quotes_list, coin['coin_name'])
    coin['price_A']=price
    coin['timestamp_A']=time_stmp
save_data(coin_list)

time.sleep(int(config['time_frame']))

quotes=get_quotes_data()

for coin in coin_list:
    price, time_stmp=check_price(quotes, coin['coin_name'])
    coin['price_B']=price
    coin['timestamp_B']=time_stmp
save_data(coin_list)
logging.debug(f'output_data.json обновлен')

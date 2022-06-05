import json
import logging
import os
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s_%(levelname)s: %(message)s')

def get_config():
    with open('config.json', 'r') as config_file:
        config=json.loads(config_file.read())
        config_file.close()
        return config

def get_token():
    with open('token.json', 'r') as config_file:
        config=json.loads(config_file.read())
        config_file.close()
        return config

def save_data(json_data, file_name):    #Сохранение данных json в файл
    if not os.path.exists('temp'): os.makedirs('temp') 
    with open(os.path.join('.','temp',file_name), 'w') as response_data_file:
        response_data_file.write(json.dumps(json_data, indent=4, sort_keys=True))
        response_data_file.close()

def kill_bot():
    exit()
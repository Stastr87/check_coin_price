
import time
import logging
import telebot
from telebot import types
import coin_module
import tools_module
import sys
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s_%(levelname)s: %(message)s')



bot = telebot.TeleBot(tools_module.get_token()["something_unimportant"])


#Добавить команду /stop
#Реализовать изменение конфига

@bot.message_handler(commands=["start"])
def start(m, res=False):
    bot.send_message(
        m.chat.id, 'Бот ослеживает котировки согласно настройкам. Нажмите "Запуск".')
    # Добавляем две кнопки
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Запуск")
    item2 = types.KeyboardButton("Настройки")
    markup.add(item1)
    markup.add(item2)


@bot.message_handler(content_types=["text"])
def check_quotes(m, res=False):
    if m.text.strip()=='Запуск':
        bot.send_message(m.chat.id, 'Бот начал отслеживать котировки')
        coin_module.update_coin_list(m, bot)

    elif  m.text.strip()=="Настройки":   #реализовать изменение конфига
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(text=f'Интервал (сек.) = {tools_module.get_config()["time_frame"]}', callback_data="time_frame"))
        markup.add(telebot.types.InlineKeyboardButton(text=f'Пороговое значение (%) = {tools_module.get_config()["alert_threshold"]}', callback_data="alert_threshold"))
        bot.send_message(m.chat.id, text="Какие настройки изменить?", reply_markup=markup)

@bot.message_handler(content_types=['text'])
def set_time_frame(m, setting_name):
    #Проверка ввода числа 
    some_Value=m.text.lower()
    if tools_module.get_number(some_Value)==False:
        bot.send_message(m.chat.id, 'Ошибка примения настроек!')
    else:
        tools_module.change_config(setting_name,some_Value)
        bot.send_message(m.chat.id, f'Настройки сохранены!')

@bot.message_handler(content_types=['text'])
def set_threshold(m, setting_name):
    #Проверка ввода числа 
    some_Value=m.text.lower()
    if tools_module.get_float_number(some_Value)==False:
        bot.send_message(m.chat.id, 'Ошибка примения настроек!')
    else:
        tools_module.change_config(setting_name,some_Value)
        bot.send_message(m.chat.id, f'Настройки сохранены!')


@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    answer = ''
    if call.data == 'time_frame':
        answer=bot.send_message(call.message.chat.id, 'Укажите время в секундах...')
        bot.register_next_step_handler(answer,set_time_frame, call.data)
    elif call.data == 'alert_threshold':
        answer=bot.send_message(call.message.chat.id, 'Укажите порог в процентах...')
        bot.register_next_step_handler(answer,set_threshold, call.data)

    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)    #Удалить клавиатуру из чата 

##------исполняемый код скрипта-------
bot.polling(none_stop=True, interval=0)

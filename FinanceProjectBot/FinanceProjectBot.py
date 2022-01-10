from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
import os
import re

import telebot
from telebot import custom_filters, SimpleCustomFilter
from keyboa import Keyboa
from flask import Flask, request

from BotAdditional import parser, act_EXP_INC, check_existence, is_date_filter_exist
from bot_matplotlib.matplotlib import get_balance_pie_chart, get_categories_type_pie_chart, get_category_pie_chart
from bot_request.request import get_categories, get_operations, del_operations, get_operation, add_categories, \
    add_operations, partial_update_operations, add_or_update_api_user, del_categories, partial_update_api_users, \
    get_api_users_list

load_dotenv()

# !!!! Edit before deploy!!!!
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")


bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)


# Add Own custom filter
class IsFloatFilter(SimpleCustomFilter):
    key = 'is_float'

    def check(self, message):
        try:
            float(message.text)
        except ValueError:
            return False
        return True


# Add Own custom filter
class IsCorrectDateFilter(SimpleCustomFilter):
    key = 'is_correct_date'

    def check(self, message):
        try:
            text_date = datetime.strptime(message.text, '%d-%m-%Y').date()
        except ValueError:
            return False
        if datetime.now().date() <= text_date:
            return False
        return True


# class for states
class CategoryStates:
    name = 1


# class for states
class OperationStates:
    title = 11
    description = 12
    amount = 13


# class for states
class PeriodStates:
    period = 21
    period_end = 22


@bot.message_handler(commands=['start'])
def send_welcome(message):
    add_or_update_api_user(chat_id=message.chat.id, first_name=message.chat.first_name,
                           last_name=message.chat.last_name, username=message.chat.username)
    bot.send_message(chat_id=message.chat.id, text=f'Hello {message.chat.first_name}!\n'
                                                   f'Для начала работы введите "/fin".\n'
                                                   f'Для задания периода только за\n'
                                                   f'который будут отображаться операции \n'
                                                   f'ведите "/per".')


@bot.message_handler(commands=['help'])
def send_welcome(message):
    bot.send_message(chat_id=message.chat.id, text='Незнание - сила!')


@bot.message_handler(commands=['fin'])
def start(message):
    add_or_update_api_user(chat_id=message.chat.id, first_name=message.chat.first_name,
                           last_name=message.chat.last_name, username=message.chat.username)
    kb_start = Keyboa(items={
        'Начать работу': 'main_menu',
    }).keyboard
    bot.send_message(chat_id=message.chat.id, reply_markup=kb_start, text=f'{message.chat.first_name}, начнем работу?')


@bot.message_handler(commands=['per'])
def start(message):
    add_or_update_api_user(chat_id=message.chat.id, first_name=message.chat.first_name,
                           last_name=message.chat.last_name, username=message.chat.username)
    kb_start = Keyboa(items={
        'Далее': 'period',
    }).keyboard
    bot.send_message(chat_id=message.chat.id, reply_markup=kb_start,
                     text=f'{message.chat.first_name}, для указание периода\n'
                          f'отображения операций нажмите далее.')


@bot.callback_query_handler(func=lambda call: call.data == 'period')
def reset_period(message):
    chat_id = message.message.chat.id
    message_id = message.message.id
    user_data = get_api_users_list(chat_id=chat_id)[0]
    date_filter = 'не установлен.\nОтображаются все операции.'
    if user_data['date_filter_end'] is None:
        date_filter_end = datetime.now().date()
    else:
        date_filter_end = date.fromisoformat(user_data['date_filter_end'])
    if user_data['date_filter_start'] is not None:
        date_filter_start = date.fromisoformat(user_data['date_filter_start'])
        date_filter = f'\n' \
                      f'с  - {date_filter_start.strftime("%d %B %Y")}\n' \
                      f'по - {date_filter_end.strftime("%d %B %Y")}'
    kb_start = Keyboa(items=[
        {'✅ Установить период': 'set_period'},
        {'✳ Сбросить период': 'reset_period'},
        {'❎ Закрыть': 'close_period'},
    ]).keyboard
    bot.edit_message_text(chat_id=chat_id, reply_markup=kb_start, message_id=message_id,
                          text=f'Текущий период: {date_filter}')


@bot.callback_query_handler(func=lambda call: call.data == 'reset_period')
def reset_period(message):
    chat_id = message.message.chat.id
    message_id = message.message.id
    user_data = get_api_users_list(chat_id=chat_id)[0]
    if user_data['pin_message_id'] is not None:
        try:
            bot.delete_message(chat_id=chat_id, message_id=user_data['pin_message_id'])
        except Exception as ex:
            print(ex)
        user_data['pin_message_id'] = None
    user_data['date_filter_start'] = None
    user_data['date_filter_end'] = None
    partial_update_api_users(id=user_data['id'],
                             date_filter_start=user_data['date_filter_start'],
                             date_filter_end=user_data['date_filter_end'],
                             pin_message_id=user_data['pin_message_id'])
    kb_previous = Keyboa(items=[
        {'⬅ Вернуться на шаг назад ': 'period'},
        {'❎ Закрыть': 'close_period'},
    ]).keyboard
    bot.edit_message_text(chat_id=chat_id, message_id=message_id, reply_markup=kb_previous,
                          text=f'Период сброшен. Отображаются все операции.')


@bot.callback_query_handler(func=lambda call: call.data == 'set_period')
def set_period(message):
    chat_id = message.message.chat.id
    message_id = message.message.id
    kb_previous = Keyboa(items={
        '⬅ Вернуться на шаг назад ': 'period'
    }).keyboard
    kb_per = Keyboa(items=[
        {'За неделю': 'we'},
        {'За месяц': 'mo'},
        {'За три месяца': 'm3'},
        {'За пол года': 'hy'},
        {'Указать произвольную дату': 'xx'},
    ], front_marker="&pr1=", back_marker="$", items_in_row=2).keyboard
    kb_all = Keyboa.combine(keyboards=(kb_per, kb_previous))
    bot.edit_message_text(chat_id=chat_id, message_id=message_id, reply_markup=kb_all,
                          text=f'Выберите период')


@bot.callback_query_handler(func=lambda call: call.data == 'close_period')
def set_period(message):
    chat_id = message.message.chat.id
    message_id = message.message.id
    bot.delete_message(chat_id=chat_id, message_id=message_id)


@bot.callback_query_handler(func=lambda call: re.match(r'^&pr1=', call.data))
def callback_inline(message):
    chat_id = message.message.chat.id
    message_id = message.message.id
    data = parser(message.data)
    user_data = get_api_users_list(chat_id=chat_id)[0]
    if 'pin_message_id' in user_data.keys():
        try:
            bot.delete_message(chat_id=chat_id, message_id=user_data['pin_message_id'])
        except Exception as ex:
            print(ex)
    if data[1] == 'we':
        user_data['date_filter_start'] = (datetime.now().date() - relativedelta(weeks=1)).isoformat()
    elif data[1] == 'mo':
        user_data['date_filter_start'] = (datetime.now().date() - relativedelta(months=1)).isoformat()
    elif data[1] == 'm3':
        user_data['date_filter_start'] = (datetime.now().date() - relativedelta(months=3)).isoformat()
    elif data[1] == 'hy':
        user_data['date_filter_start'] = (datetime.now().date() - relativedelta(months=6)).isoformat()
    if data[1] != 'xx':
        user_data['date_filter_end'] = None
        kb_previous = Keyboa(items={
            '⬅ Вернуться назад ': 'period'
        }).keyboard
        pin_text = f'‼ Установлен период ‼\n' \
                   f'с  - {date.fromisoformat(user_data["date_filter_start"]).strftime("%d %B %Y")}\n' \
                   f'по - {datetime.now().date().strftime("%d %B %Y")} \n' \
                   f'Операции за рамками периода не отображаются'
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=pin_text)
        user_data['pin_message_id'] = message_id
        partial_update_api_users(id=user_data['id'],
                                 date_filter_start=user_data['date_filter_start'],
                                 date_filter_end=user_data['date_filter_end'],
                                 pin_message_id=user_data['pin_message_id'])
        bot.pin_chat_message(chat_id=chat_id, message_id=message_id)
        bot.send_message(chat_id=chat_id, reply_markup=kb_previous, text=f'Период установлен.')
    else:
        bot.set_state(chat_id, PeriodStates.period)
        with bot.retrieve_data(chat_id) as r_data:
            bot.delete_message(chat_id=chat_id, message_id=message_id)
            r_data['backstep'] = 'period'
        bot.send_message(chat_id=chat_id, text='Введите дату начала периода\n'
                                               'формат "dd-mm-yyyy"\n'
                                               '(для отмены введите "/cancel")')


@bot.callback_query_handler(func=lambda call: call.data == 'main_menu')
def kb_start(message):
    chat_id = message.message.chat.id
    message_id = message.message.id
    user_data = get_api_users_list(chat_id=chat_id)[0]
    if user_data['date_filter_start'] is not None:
        alert_text = f"‼Внимание! Установлен период.‼\n" \
                     f"‼Введите '/per' для изменения.‼\n\n"
    else:
        alert_text = ''
    kb_balance = Keyboa(items={
        '📊 Баланс': 'show_balance',
    }, front_marker="&st1=", back_marker="$").keyboard
    kb_inc_exp = Keyboa(items=[
        {'Доходы': 'INC'},
        {'Расходы': 'EXP'},
    ], front_marker="&st1=", back_marker="$", items_in_row=2).keyboard
    kb_first = Keyboa.combine(keyboards=(kb_balance, kb_inc_exp))
    if message.message.text is not None:
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, reply_markup=kb_first,
                              text=alert_text + 'Выберите необходимое действие')
    else:
        bot.delete_message(chat_id=chat_id, message_id=message_id)
        bot.send_message(chat_id=chat_id, reply_markup=kb_first, text=alert_text + 'Выберите необходимое действие')


@bot.callback_query_handler(func=lambda call: re.match(r'^&st1=', call.data))
def callback_inline(message):
    chat_id = message.message.chat.id
    message_id = message.message.id
    first_name = message.message.chat.first_name
    data = parser(message.data)
    if data[1] in ('INC', 'EXP'):
        act = act_EXP_INC(data[1])
        kb_show = Keyboa(items=[
            {f'📊 Диаграмма {act}ов': f'show_diagram'},
            {f'📄 Просмотреть {act}ы': f'show'},
        ], front_marker="&st2=", back_marker=message.data, items_in_row=2).keyboard
        kb_act = Keyboa(items=[
            {f'➕ Добавить {act}': 'add'},
            {f'❌ Удалить {act}': 'del'},
        ], front_marker="&st2=", back_marker=message.data, items_in_row=2).keyboard
        kb_cat = Keyboa(items=[
            {f'🗂 Категории {act}ов': 'cat'},
        ], front_marker="&st2=", back_marker=message.data, items_in_row=1).keyboard
        kb_menu = Keyboa(items={
            '⬆ Вернуться в основное меню': 'main_menu'
        }).keyboard
        kb_second = Keyboa.combine(keyboards=(kb_show, kb_act, kb_cat, kb_menu))
        if message.message.text is not None:
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, reply_markup=kb_second,
                                  text='Выберите следующее действие')
        else:
            bot.delete_message(chat_id=chat_id, message_id=message_id)
            bot.send_message(chat_id=chat_id, reply_markup=kb_second, text='Выберите следующее действие')
    if data[1] == 'show_balance':
        kb_menu = Keyboa(items={
            '⬆ Вернуться в основное меню': 'main_menu'
        }).keyboard
        if check_existence(chat_id=chat_id):
            get_balance_pie_chart(chat_id=chat_id)
            bot.delete_message(chat_id=chat_id, message_id=message_id)
            bot.send_photo(chat_id=chat_id, photo=open(f'picts/{chat_id}_balance.png', 'rb'), reply_markup=kb_menu,
                           caption=f'{first_name}, баланс Ваших расходов и доходов:')
            os.remove(f'picts/{chat_id}_balance.png')
        else:
            bot.edit_message_text(text='Нет данных для формирования диаграммы', chat_id=chat_id, message_id=message_id,
                                  reply_markup=kb_menu)


@bot.callback_query_handler(func=lambda call: re.match(r'^&st2=', call.data))
def callback_inline(message):
    chat_id = message.message.chat.id
    message_id = message.message.id
    first_name = message.message.chat.first_name
    data = parser(message.data)
    items = []
    kb_previous = Keyboa(items={
        '⬅ Вернуться на шаг назад ': '&' + message.data.split('&')[-1]
    }).keyboard
    kb_menu = Keyboa(items={
        '⬆ Вернуться в основное меню': 'main_menu'
    }).keyboard
    act = act_EXP_INC(data[1])
    if data[2] == 'add':
        categories = get_categories(cat_type=data[1], chat_id=chat_id)
        if categories != []:
            for element in categories:
                items.append({element['name']: element['id']})
            kb_cat = Keyboa(items=items, front_marker="&st3=", back_marker=message.data, items_in_row=3).keyboard
        else:
            items.append({f'🚫 нет категорий для отображения 🚫': 1})
            kb_cat = Keyboa(items=items, items_in_row=1).keyboard
        kb_add = Keyboa(items=[{'➕ Добавить категорию': 'newcat'}], front_marker="&st3=", back_marker=message.data,
                        items_in_row=3).keyboard
        kb_second = Keyboa.combine(keyboards=(kb_cat, kb_add, kb_previous, kb_menu))
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, reply_markup=kb_second,
                              text='Выберите категорию')
    elif data[2] == 'del':
        additional = is_date_filter_exist(chat_id=chat_id)
        operations = get_operations(chat_id=chat_id, cat_type=data[1], **additional)
        if operations != []:
            for element in operations:
                items.append({element['title']: element['id']})
            kb_cat = Keyboa(items=items, front_marker="&st3=", back_marker=message.data, items_in_row=2).keyboard
        else:
            items.append({f'🚫 нет {act}ов для отображения 🚫': 1})
            kb_cat = Keyboa(items=items, items_in_row=1).keyboard
        kb_second = Keyboa.combine(keyboards=(kb_cat, kb_previous, kb_menu))
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, reply_markup=kb_second,
                              text='Что хотите удалить?')
    elif data[2] == 'show_diagram':
        if check_existence(chat_id=chat_id, cat_type=data[1]):
            get_categories_type_pie_chart(chat_id=chat_id, cat_type=data[1])
            bot.delete_message(chat_id=chat_id, message_id=message_id)
            bot.send_photo(chat_id=chat_id, photo=open(f'picts/{chat_id}_categories_type.png', 'rb'),
                           reply_markup=kb_previous,
                           caption=f'{first_name}, диаграмма Ваших {act}ов:')
            os.remove(f'picts/{chat_id}_categories_type.png')
        else:
            bot.edit_message_text(text='Нет данных для формирования диаграммы', chat_id=chat_id,
                                  message_id=message_id,
                                  reply_markup=kb_previous)
    elif data[2] == 'show':
        kb_show = Keyboa(items=[
            {'Показать все': 'all'},
            {'Показать по категориям': 'cats'},
        ], front_marker="&st3=", back_marker=message.data, items_in_row=2).keyboard
        kb_second = Keyboa.combine(keyboards=(kb_show, kb_previous, kb_menu))
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, reply_markup=kb_second,
                              text=f'Выберите необходимый вариант')
    elif data[2] == 'cat':
        kb_cat_all = Keyboa(items=[
            {'🗂 Показать все доступные категории': 'all'},
        ], front_marker="&st3=", back_marker=message.data, items_in_row=2).keyboard
        kb_cat = Keyboa(items=[
            {'📂 Используемые категории': 'used'},
            {'📁 Неиспользуемые категории': 'unused'},
        ], front_marker="&st3=", back_marker=message.data, items_in_row=2).keyboard
        kb_del = Keyboa(items=[
            {'❌ Удалить неиспользуемые категории': 'del'},
        ], front_marker="&st3=", back_marker=message.data, items_in_row=2).keyboard
        kb_second = Keyboa.combine(keyboards=(kb_cat_all, kb_cat, kb_del, kb_previous, kb_menu))
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, reply_markup=kb_second,
                              text=f'Выберите необходимый вариант')


@bot.callback_query_handler(func=lambda call: re.match(r'^&st3=', call.data))
def callback_inline(message):
    chat_id = message.message.chat.id
    message_id = message.message.id
    data = parser(message.data)
    items = []
    act = act_EXP_INC(data[1])
    kb_previous = Keyboa(items={
        '⬅ Вернуться на шаг назад': f'&st2={data[2]}&st1={data[1]}$'
    }).keyboard
    kb_menu = Keyboa(items={
        '⬆ Вернуться в основное меню': 'main_menu'
    }).keyboard
    # print(message.data)
    if data[2] == 'show':
        if data[3] == 'all':
            additional = is_date_filter_exist(chat_id=chat_id)
            operations = get_operations(chat_id=chat_id, cat_type=data[1], **additional)
            if operations != []:
                for element in operations:
                    items.append({element['title']: element['id']})
                kb_operations = Keyboa(items=items, front_marker="&st4=op", back_marker=message.data,
                                       items_in_row=2).keyboard
            else:
                items.append({f'🚫 нет {act}ов для отображения 🚫': 1})
                kb_operations = Keyboa(items=items, items_in_row=1).keyboard
            kb_all = Keyboa.combine(keyboards=(kb_operations, kb_previous, kb_menu))
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, reply_markup=kb_all,
                                  text=f'Выберите {act} для детального отображения.')
        if data[3] == 'cats':
            categories = get_categories(cat_type=data[1], chat_id=chat_id, unused=False)
            if categories != []:
                for element in categories:
                    items.append({element['name']: element['id']})
                kb_cat = Keyboa(items=items, front_marker="&st4=ct", back_marker=message.data, items_in_row=3).keyboard
            else:
                items.append({f'🚫 нет категорий для отображения 🚫': 1})
                kb_cat = Keyboa(items=items, items_in_row=1).keyboard
            kb_all = Keyboa.combine(keyboards=(kb_cat, kb_previous, kb_menu))
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, reply_markup=kb_all,
                                  text=f'Выберите категорию.')
    elif data[2] == 'add':
        if data[3] == 'newcat':
            bot.set_state(chat_id, CategoryStates.name)
            with bot.retrieve_data(chat_id) as r_data:
                bot.delete_message(chat_id=chat_id, message_id=message_id)
                r_data['cat_type'] = data[1]
                r_data['backstep'] = '&' + message.data.split('&', maxsplit=2)[2]
            bot.send_message(chat_id=chat_id, text='Введите название категории\n(для отмены введите "/cancel")')
        elif data[3].isnumeric():
            bot.set_state(chat_id, OperationStates.title)
            with bot.retrieve_data(chat_id) as r_data:
                bot.delete_message(chat_id=chat_id, message_id=message_id)
                r_data['category'] = data[3]
                r_data['chat_id'] = chat_id
                r_data['backstep'] = '&' + message.data.split('&', maxsplit=3)[3]
                r_data['operation'] = 'create'
            bot.send_message(chat_id=chat_id, text='Введите название операции\n(для отмены введите "/cancel")')
    elif data[2] == 'del':
        del_operations(id=data[3])
        kb_next = Keyboa(items={
            'Продолжить ➡': f'&st2={data[2]}&st1={data[1]}$'
        }).keyboard
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, reply_markup=kb_next,
                              text=f'Операция удалена.')
    elif data[2] == 'cat':
        if data[3] == 'all':
            categories = get_categories(cat_type=data[1], chat_id=chat_id)
            if categories != []:
                for element in categories:
                    items.append({element['name']: element['id']})
                kb_cat = Keyboa(items=items, front_marker="&st4=", back_marker=message.data, items_in_row=3).keyboard
            else:
                items.append({f'🚫 нет категорий для отображения 🚫': 1})
                kb_cat = Keyboa(items=items, items_in_row=1).keyboard
            kb_all = Keyboa.combine(keyboards=(kb_cat, kb_previous, kb_menu))
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, reply_markup=kb_all,
                                  text=f'Список доступных категорий {act}ов:')
        elif data[3] == 'used':
            categories = get_categories(cat_type=data[1], chat_id=chat_id, unused=False)
            if categories != []:
                for element in categories:
                    items.append({element['name']: element['id']})
                kb_cat = Keyboa(items=items, front_marker="&st4=", back_marker=message.data, items_in_row=3).keyboard
            else:
                items.append({f'🚫 нет категорий для отображения 🚫': 1})
                kb_cat = Keyboa(items=items, items_in_row=1).keyboard
            kb_all = Keyboa.combine(keyboards=(kb_cat, kb_previous, kb_menu))
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, reply_markup=kb_all,
                                  text=f'Список используемых категорий {act}ов:')
        elif data[3] == 'unused':
            categories = get_categories(cat_type=data[1], chat_id=chat_id, unused=True)
            if categories != []:
                for element in categories:
                    items.append({element['name']: element['id']})
                kb_cat = Keyboa(items=items, front_marker="&st4=", back_marker=message.data, items_in_row=3).keyboard
            else:
                items.append({f'🚫 нет категорий для отображения 🚫': 1})
                kb_cat = Keyboa(items=items, items_in_row=1).keyboard
            kb_all = Keyboa.combine(keyboards=(kb_cat, kb_previous, kb_menu))
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, reply_markup=kb_all,
                                  text=f'Список неиспользуемых категорий {act}ов:')
        elif data[3] == 'del':
            categories = get_categories(cat_type=data[1], chat_id=chat_id, unused=True)
            if categories != []:
                for element in categories:
                    items.append({element['name']: element['id']})
                kb_cat = Keyboa(items=items, front_marker="&st4=del", back_marker=message.data, items_in_row=3).keyboard
            else:
                items.append({f'🚫 нет категорий для отображения 🚫': 1})
                kb_cat = Keyboa(items=items, items_in_row=1).keyboard
            kb_all = Keyboa.combine(keyboards=(kb_cat, kb_previous, kb_menu))
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, reply_markup=kb_all,
                                  text=f'Выберите категорию для удаления:')


@bot.callback_query_handler(func=lambda call: re.match(r'^&st4=', call.data))
def callback_inline(message):
    chat_id = message.message.chat.id
    message_id = message.message.id
    data = parser(message.data)
    items = []
    act = act_EXP_INC(data[1])
    kb_previous = Keyboa(items={
        '⬅ Вернуться на шаг назад': f'&st3={data[3]}&st2={data[2]}&st1={data[1]}$'
    }).keyboard
    kb_menu = Keyboa(items={
        '⬆ Вернуться в основное меню': 'main_menu'
    }).keyboard
    if data[2] == 'show':
        if data[4][:2] == 'op':
            operation = get_operation(chat_id, data[4][2:])
            text = f'Название: {operation["title"]}\nОписание: {operation["description"]}\n' \
                   f'Сумма: {operation["amount"]}\n' \
                   f'Категория: {operation["category"]["name"]}\nСоздано: {operation["created_at"]}'
            kb_edit = Keyboa(items=[{'✏ Редактировать операцию': 'edit'}], front_marker="&st5=",
                             back_marker=message.data).keyboard
            kb_all = Keyboa.combine(keyboards=(kb_edit, kb_previous, kb_menu))
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, reply_markup=kb_all,
                                  text=text)
        if data[4][:2] == 'ct':
            additional = is_date_filter_exist(chat_id=chat_id)
            operations = get_operations(chat_id=chat_id, category=data[4][2:], **additional)
            if operations != []:
                for element in operations:
                    items.append({element['title']: element['id']})
                kb_operations = Keyboa(items=items, front_marker="&st5=", back_marker=message.data,
                                       items_in_row=2).keyboard
                kb_diag = Keyboa(items=[
                    {f'📊 Диаграмма {act}ов по категории': f'diag'},
                ], front_marker="&st5=", back_marker=message.data).keyboard
                kb_all = Keyboa.combine(keyboards=(kb_diag, kb_operations, kb_previous, kb_menu))
            else:
                items.append({f'🚫 нет {act}ов для отображения 🚫': 'None'})
                kb_operations = Keyboa(items=items, front_marker="&st5=", back_marker=message.data,
                                       items_in_row=2).keyboard
                kb_all = Keyboa.combine(keyboards=(kb_operations, kb_previous, kb_menu))
            if message.message.text is not None:
                bot.edit_message_text(chat_id=chat_id, message_id=message_id, reply_markup=kb_all,
                                      text=f'Выберите {act} для детального отображения.')
            else:
                bot.delete_message(chat_id=chat_id, message_id=message_id)
                bot.send_message(chat_id=chat_id, reply_markup=kb_all,
                                 text=f'Выберите {act} для детального отображения.')
    elif data[2] == 'cat':
        if data[3] == 'del':
            id_cat_del = data[4][3:]
            del_categories(id_cat_del)
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, reply_markup=kb_previous,
                                  text=f'Категория удалена.')


@bot.callback_query_handler(func=lambda call: re.match(r'^&st5=', call.data))
def callback_inline(message):
    chat_id = message.message.chat.id
    message_id = message.message.id
    data = parser(message.data)
    act = act_EXP_INC(data[1])
    kb_previous = Keyboa(items={
        '⬅ Вернуться на шаг назад': f'&st4={data[4]}&st3={data[3]}&st2={data[2]}&st1={data[1]}$'
    }).keyboard
    kb_menu = Keyboa(items={
        '⬆ Вернуться в основное меню': 'main_menu'
    }).keyboard
    if data[5] == 'diag':
        get_category_pie_chart(chat_id=chat_id, category=data[4][2:])
        bot.delete_message(chat_id=chat_id, message_id=message_id)
        bot.send_photo(chat_id=chat_id, photo=open(f'picts/{chat_id}_category.png', 'rb'),
                       reply_markup=kb_previous,
                       caption=f'Диаграмма {act}ов по категории:')
        os.remove(f'picts/{chat_id}_category.png')
    elif data[5].isdigit():
        operation = get_operation(chat_id, data[5])
        text = f'Название: {operation["title"]}\nОписание: {operation["description"]}\n' \
               f'Сумма: {operation["amount"]}\n' \
               f'Категория: {operation["category"]["name"]}\nСоздано: {operation["created_at"]}'
        kb_edit = Keyboa(items=[{'✏ Редактировать операцию': 'edit'}], front_marker="&st6=",
                         back_marker=message.data).keyboard
        kb_all = Keyboa.combine(keyboards=(kb_edit, kb_previous, kb_menu))
        bot.edit_message_text(chat_id=chat_id, message_id=message_id, reply_markup=kb_all,
                              text=text)
    elif data[5] == 'edit':
        bot.set_state(chat_id, OperationStates.title)
        with bot.retrieve_data(chat_id) as r_data:
            bot.delete_message(chat_id=chat_id, message_id=message_id)
            r_data['id'] = data[4][2:]
            r_data['chat_id'] = chat_id
            r_data['backstep'] = '&st4=' + data[4] + '&st3=' + data[3] + \
                                 '&st2=' + data[2] + '&st1=' + data[1] + '$'
            r_data['operation'] = 'change'
        bot.send_message(chat_id=chat_id, text='Введите название операции\n(для отмены введите "/cancel")')
        pass


@bot.callback_query_handler(func=lambda call: re.match(r'^&st6=', call.data))
def callback_inline(message):
    chat_id = message.message.chat.id
    message_id = message.message.id
    data = parser(message.data)
    if data[6] == 'edit':
        bot.set_state(chat_id, OperationStates.title)
        with bot.retrieve_data(chat_id) as r_data:
            bot.delete_message(chat_id=chat_id, message_id=message_id)
            r_data['id'] = data[5]
            r_data['chat_id'] = chat_id
            r_data['category'] = data[4][2:]
            r_data['backstep'] = '&st5=' + data[5] + '&st4=' + data[4] + '&st3=' + data[3] + \
                                 '&st2=' + data[2] + '&st1=' + data[1] + '$'
            r_data['operation'] = 'change'
        bot.send_message(chat_id=chat_id, text='Введите название операции\n(для отмены введите "/cancel")')


# below states handlers
@bot.message_handler(state="*", commands='cancel')
def any_state(message):
    """
    Cancel state
    """
    with bot.retrieve_data(message.from_user.id) as data:
        kb_next = Keyboa(items={
            'Продолжить ➡': data['backstep']
        }).keyboard
    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
    bot.send_message(message.chat.id, "Ввод отменен", reply_markup=kb_next)
    bot.delete_state(message.from_user.id)


@bot.message_handler(state=CategoryStates.name)
def category_name_get(message):
    with bot.retrieve_data(message.from_user.id) as data:
        data['name'] = message.text
        backstep = data['backstep']
        add_categories(name=message.text, cat_type=data['cat_type'], chat_id=message.chat.id)
    kb_next = Keyboa(items={
        'Продолжить ➡': backstep
    }).keyboard
    bot.send_message(chat_id=message.chat.id, text=f'Категория "{message.text}" добавлена.', reply_markup=kb_next)
    bot.delete_state(message.from_user.id)


@bot.message_handler(state=OperationStates.title)
def operation_title_get(message):
    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
    bot.set_state(message.from_user.id, OperationStates.description)
    with bot.retrieve_data(message.from_user.id) as data:
        data['title'] = message.text
    bot.send_message(chat_id=message.chat.id, text=f'Введите описание\n(для отмены введите "/cancel")')


@bot.message_handler(state=OperationStates.description)
def operation_description_get(message):
    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
    bot.set_state(message.from_user.id, OperationStates.amount)
    with bot.retrieve_data(message.from_user.id) as data:
        data['description'] = message.text
    bot.send_message(chat_id=message.chat.id, text=f'Введите сумму\n(для отмены введите "/cancel")')


@bot.message_handler(state=OperationStates.amount, is_float=True)
def operation_amount_get(message):
    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
    with bot.retrieve_data(message.from_user.id) as data:
        data['amount'] = message.text
        backstep = data['backstep']
        if data['operation'] == 'create':
            add_operations(title=data['title'], description=data['description'], amount=data['amount'],
                           category=data['category'], chat_id=data['chat_id'])
        elif data['operation'] == 'change':
            keys = {}
            for element in data:
                if data[element] is not None:
                    keys[element] = data[element]
            partial_update_operations(**keys)
    kb_next = Keyboa(items={
        'Продолжить ➡': backstep
    }).keyboard
    bot.send_message(chat_id=message.chat.id, text=f'Продолжить', reply_markup=kb_next)
    bot.delete_state(message.from_user.id)


@bot.message_handler(state=OperationStates.amount, is_float=False)
def operation_amount_incorrect(message):
    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
    bot.send_message(message.chat.id, 'Введенное значение не является числом. Повторите ввод.\n'
                                      '(для отмены введите "/cancel")')


@bot.message_handler(state=PeriodStates.period, is_correct_date=True)
def period_period_get(message):
    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
    bot.set_state(message.from_user.id, PeriodStates.period_end)
    with bot.retrieve_data(message.from_user.id) as data:
        data['period'] = datetime.strptime(message.text, '%d-%m-%Y').date()
    bot.send_message(chat_id=message.chat.id, text='Введите дату окончания периода\n'
                                                   'формат "dd-mm-yyyy"\n'
                                                   '(для отмены введите "/cancel")')


@bot.message_handler(state=PeriodStates.period, is_correct_date=False)
@bot.message_handler(state=PeriodStates.period_end, is_correct_date=False)
def period_false_get(message):
    bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
    bot.send_message(message.chat.id, 'Введенное значение не корректно. Повторите ввод\n'
                                      '(для отмены введите "/cancel")')


@bot.message_handler(state=PeriodStates.period_end, is_correct_date=True)
def period_period_end_get(message):
    bot.set_state(message.from_user.id, PeriodStates.period_end)
    chat_id = message.chat.id
    message_id = message.message_id
    user_data = get_api_users_list(chat_id=chat_id)[0]
    with bot.retrieve_data(message.from_user.id) as data:
        period = data['period']
        period_end = datetime.strptime(message.text, '%d-%m-%Y').date()
        backstep = data['backstep']
    pin_text = f'‼ Установлен период ‼\n' \
               f'с  - {period.strftime("%d %B %Y")}\n' \
               f'по - {period_end.strftime("%d %B %Y")} \n' \
               f'Операции за рамками периода не отображаются'
    kb_next = Keyboa(items={
        'Продолжить ➡': backstep
    }).keyboard
    bot.edit_message_text(chat_id=chat_id, message_id=message_id - 1, text=pin_text)
    user_data['pin_message_id'] = message_id - 1
    user_data['date_filter_start'] = period.isoformat()
    user_data['date_filter_end'] = period_end.isoformat()
    bot.pin_chat_message(chat_id=chat_id, message_id=message_id - 1)
    bot.send_message(chat_id=chat_id, text=f'Период c установлен.',
                     reply_markup=kb_next)
    partial_update_api_users(id=user_data['id'],
                             date_filter_start=user_data['date_filter_start'],
                             date_filter_end=user_data['date_filter_end'],
                             pin_message_id=user_data['pin_message_id'])
    bot.delete_state(message.from_user.id)


# repeater
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    print(message.text)
    bot.reply_to(message, message.text)


bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.add_custom_filter(IsFloatFilter())
bot.add_custom_filter(IsCorrectDateFilter())


# # set saving states into file.
# bot.enable_saving_states()  # you can delete this if you do not need to save states

# bot.infinity_polling()

@server.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL + BOT_TOKEN)
    return "!", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))

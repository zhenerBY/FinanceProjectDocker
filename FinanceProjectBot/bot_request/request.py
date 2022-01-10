import os

from dotenv import load_dotenv
import requests
import json

load_dotenv()

# !!!! Edit before deploy!!!!
HOST_API = os.getenv("HOST_API")
APIKEY = os.getenv("APIKEY")


# Примеры работы для бота
def api_request(method=None,
                url=None,
                headers=None,
                json=None):
    headers = {} if headers is None else headers
    headers.update(
        {
            'Authorization': 'Api-Key ' + APIKEY,
        }
    )
    req = requests.Request(
        method=method,
        url=url,
        headers=headers,
        json=json
    )
    r = req.prepare()
    s = requests.Session()
    return s.send(r)


# С аргументов выводит только текущего пользователя, без - всех
def get_api_users_list(chat_id: int = None) -> list:
    if chat_id is not None:
        data = {
            'chat_id': chat_id,
        }
    else:
        data = {}
    url = HOST_API + 'apiusers/'
    users_data = api_request(method='GET', json=data, url=url)
    json_users_data = users_data.json()
    return json_users_data


# use kwargs name from ApiUserModel. Required 'id' or 'chat_id'
def partial_update_api_users(id: int = None, **kwargs) -> dict:
    data = {}
    data['id'] = id
    for element in kwargs:
        data[element] = kwargs[element]
    url = HOST_API + 'apiusers/' + str(id) + '/'
    response = api_request(method='PATCH', json=data, url=url)
    json_responce = response.json()
    return json_responce


def add_api_users(chat_id, first_name: str = None, last_name: str = None, username: str = None) -> dict:
    data = {
        'chat_id': chat_id,
        'first_name': first_name,
        'last_name': last_name,
        'username': username,
    }
    url = HOST_API + 'apiusers/'
    users_data = api_request(method='POST', json=data, url=url)
    json_users_data = users_data.json()
    json_users_data['status_code'] = users_data.status_code
    return json_users_data


def add_or_update_api_user(chat_id: int, **kwargs) -> dict:
    response = get_api_users_list(chat_id=chat_id)
    if response == []:
        return add_api_users(chat_id, **kwargs)
    update_dict = {}
    for elemet in kwargs:
        if kwargs[elemet] == response[0][elemet]:
            pass
        else:
            update_dict[elemet] = kwargs[elemet]
    if update_dict != {}:
        partial_update_api_users(id=response[0]['id'], **update_dict)
    return response[0]


# С аргументом - только операции пользователя, без - все
# Set the value 'cat_type' 'INC'|'EXP' for separated list
# !!! Do not use at the same time 'cat_type' and 'category'
def get_operations(chat_id: int = None, cat_type: str = None, category: int = None, date_filter_start: str = None,
                   date_filter_end: str = None) -> list:
    data = {}
    if chat_id is not None:
        data['chat_id'] = chat_id
    if cat_type is not None:
        data['cat_type'] = cat_type
    if category is not None:
        data['category'] = category
    if date_filter_start is not None:
        data['date_filter_start'] = date_filter_start
    if date_filter_end is not None:
        data['date_filter_end'] = date_filter_end
    url = HOST_API + 'operations/'
    users_data = api_request(method='GET', json=data, url=url)
    json_users_data = users_data.json()
    return json_users_data


# get detailed information
def get_operation(chat_id: int, id: int) -> dict:
    data = {
        'chat_id': chat_id,
    }
    url = HOST_API + 'ext_operations/' + str(id) + '/'
    users_data = api_request(method='GET', json=data, url=url)
    json_users_data = users_data.json()
    return json_users_data


# get list of dict {name:id}
def get_list_of_name_operations(chat_id: int, cat_type: str) -> list:
    data = {
        'chat_id': chat_id,
    }
    url = HOST_API + 'ext_operations/'
    users_data = api_request(method='GET', json=data, url=url)
    json_users_data = users_data.json()
    tmp = []
    for item in json_users_data:
        if item['category'][cat_type] == cat_type:
            tmp.append({item['name']: item})
    json_users_data = tmp
    return json_users_data


# создание операции. Если указан chat_id -> user игнорируется
def add_operations(title: str, description: str, amount: float, category: int, user: int = 1,
                   chat_id: int = None) -> dict:
    if chat_id is not None:
        data = {
            "title": title,
            "description": description,
            "amount": amount,
            "category": category,
            "chat_id": chat_id,
        }
    else:
        data = {
            "title": title,
            "description": description,
            "amount": amount,
            "user": user,
            "category": category,
        }
    url = HOST_API + 'operations/'
    response = api_request(method='POST', json=data, url=url)
    json_responce = response.json()
    return json_responce


# use kwargs name from OperationModel
def partial_update_operations(id: int, **kwargs) -> dict:
    data = {}
    for element in kwargs:
        data[element] = kwargs[element]
    url = HOST_API + 'operations/' + str(id) + '/'
    response = api_request(method='PATCH', json=data, url=url)
    json_responce = response.json()
    return json_responce


# fake operation deletion
def del_operations(id: int) -> dict:
    data = {
        'id': id,
        'is_active': False
    }
    url = HOST_API + 'operations/' + str(id) + '/'
    response = api_request(method='PATCH', json=data, url=url)
    json_responce = response.json()
    return json_responce


# Set the value 'INC'|'EXP' for separated list
def get_categories(cat_type: str = None, chat_id: int = None, unused: bool = None) -> list:
    data = {}
    if chat_id is not None:
        data['chat_id'] = chat_id
    if cat_type is not None:
        data['cat_type'] = cat_type
    if unused is not None:
        if unused is False:
            data['unused'] = False
        else:
            data['unused'] = True
    url = HOST_API + 'categories/'
    users_data = api_request(method='GET', json=data, url=url)
    json_users_data = users_data.json()
    return json_users_data


def add_categories(name: str, cat_type: str, chat_id: int) -> dict:
    data = {
        'name': name,
        'cat_type': cat_type,
        'chat_id': chat_id,
    }
    url = HOST_API + 'categories/'
    users_data = api_request(method='POST', json=data, url=url)
    json_users_data = users_data.json()
    return json_users_data


def del_categories(id: int) -> int:
    url = HOST_API + 'categories/' + str(id) + '/'
    users_data = api_request(method='DELETE', url=url)
    return users_data.status_code


def get_balance(chat_id: int, date_filter_start: str = None, date_filter_end: str = None) -> dict:
    data = {
        'chat_id': chat_id,
    }
    if date_filter_start is not None:
        data['date_filter_start'] = date_filter_start
    if date_filter_end is not None:
        data['date_filter_end'] = date_filter_end
    url = HOST_API + 'operations/balance/'
    users_data = api_request(method='GET', json=data, url=url)
    json_users_data = users_data.json()
    return json_users_data


def get_categories_balance(chat_id: int, cat_type: str, date_filter_start: str = None,
                           date_filter_end: str = None) -> dict:
    data = {
        'chat_id': chat_id,
        'cat_type': cat_type
    }
    if date_filter_start is not None:
        data['date_filter_start'] = date_filter_start
    if date_filter_end is not None:
        data['date_filter_end'] = date_filter_end
    url = HOST_API + 'operations/cat_balance/'
    users_data = api_request(method='GET', json=data, url=url)
    json_users_data = users_data.json()
    return json_users_data

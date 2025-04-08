import asyncio
import requests
import sys
import aiohttp
from bot.config import pf_token, pf_url_rest

sys.stdout.reconfigure(encoding='utf-8')


####################### STOCK BALANCE ####################################

async def planfix_stock_balance(query=None):

    url = f"{pf_url_rest}/task/list"

    payload = {
        "offset": 0,
        "pageSize": 100,
        "filterId": "104384",
        "fields": "id,12116,5542,6640,6282,12140"
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {pf_token}"
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    all_balance_tasks = data['tasks']
    result = []
    unique_devices = set()  # Создаем множество для уникальных значений device
    unique_brands = set()

    for task in all_balance_tasks:
        id_product = task['id']
        stock_balance = 1
        product_name = None
        device = None
        brand = None
        price = None

        for custom_field in task['customFieldData']:
            if custom_field['field']['id'] == 12116:
                stock_balance = int(custom_field['value'])
            elif custom_field['field']['id'] == 5542:
                product_name = custom_field['value']['value']
            elif custom_field['field']['id'] == 6640:
                device = custom_field['value']['value']
            elif custom_field['field']['id'] == 6282:
                brand = custom_field['value']['value']
            elif custom_field['field']['id'] == 12140:
                price_value = custom_field['value']
                if isinstance(price_value, str) and price_value.isdigit():
                    price = int(price_value)

        if stock_balance is not None and product_name is not None:
            if query is None or query.lower() in product_name.lower():
                result.append((id_product, product_name,
                              stock_balance, price, device, brand))

                if device:  # Если device не пустое, добавляем его в множество
                    unique_devices.add(device)

                if brand:
                    unique_brands.add(brand)

    return result


# ####################### STOCK BALANCE (MODELS) ####################################

# async def planfix_stock_balance_models(search_query=None, offset=0, limit=RESULTS_PER_PAGE):
#     url = f"{pf_url_rest}/task/list"

#     payload = {
#         "offset": offset,
#         "pageSize": limit,
#         "filterId": "49864",
#         "fields": "id,5556,5542,6640,6282,12140"
#     }

#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {pf_token}"
#     }

#     response = requests.post(url, json=payload, headers=headers)
#     data = response.json()

#     all_models = data.get('tasks', [])
#     result = []

#     for task in all_models:
#         for custom_field in task.get('customFieldData', []):
#             if custom_field['field']['name'] == 'Модель':
#                 model_id = custom_field['value']['id']
#                 model_name = custom_field['value']['value']

#                 if search_query and search_query.lower() not in model_name.lower():
#                     continue

#                 result.append((model_id, model_name))

#     return result


####################### STOCK BALANCE (FILTER) ####################################

async def planfix_stock_balance_filter(model_id: str, operation: str):

    url = f"{pf_url_rest}/task/list"

    payload = {
        "offset": 0,
        "pageSize": 100,
        "filterId": "104384",
        "filters": [
            {
                "type": 107,
                "field": 12142,
                "operator": "equal",
                "value": operation
            },
            {
                "type": 107,
                "field": 5556,
                "operator": "equal",
                "value": model_id
            }
        ],
        "fields": "id,5556,12142,6640,6282,6274,5666,12110,5534,5532,5512"
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {pf_token}"
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    return data


####################### ALL PRODUCTION (PLANFIX) ####################################

async def planfix_all_production_filter(model_id: int):

    url = f"{pf_url_rest}/task/list"

    payload = {
        "offset": 0,
        "pageSize": 100,
        "filterId": "104400",
        "filters": [
            {
                "type": 107,
                "field": 5556, # Модель
                "operator": "equal",
                "value": model_id
            }
        ],
        "fields": "id,5556,12126,5498"
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {pf_token}"
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    return data


####################### CONTACT ####################################


async def planfix_contact(query=None):

    url = f"{pf_url_rest}/contact/list"

    payload = {
        "offset": 0,
        "pageSize": 100,
        "fields": "id,12116,5542,6640,6282,12140"
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {pf_token}"
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()


# async def main():
#     data = await planfix_stock_balance_models()
#     print(data)

# asyncio.run(main())


####################### PRODUCTION TASK ID (PLANFIX) ####################################

async def planfix_production_task_id(task_id: int):

    url = f"{pf_url_rest}/task/{task_id}"

    payload = {
        "fields": "id,5556,12126,5498"
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {pf_token}"
    }

    response = requests.get(url, json=payload, headers=headers)
    data = response.json()

    return data


####################### CREATE NEW ORDER (PLANFIX) ####################################

async def planfix_create_order(description: str, order_id: int):

    url = f"{pf_url_rest}/task/"

    payload = {
        "template": {
            "id": 46
        },
        # "name": "Новый заказ OLEDBot",
        "description": f"{description}",
        "status": {
                "id": 2
            },
        "customFieldData": [
            {
            "field": {
                "id": 5478 # Метки 
            },
            "value": [
                {
                "id": 2 # Заказ
                },
                {
                "id": 110 # OLEDBot
                },
                {
                "id": 83 # Добавить QR код
                }
            ]
            },
            {
            "field": {
                "id": 12124 # Курс USD - RUB (id заказа postgres)
            },
            "value": order_id
            }
        ]
        }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {pf_token}"
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    return data


####################### CREATE NEW PRODACTION (PLANFIX) ####################################

async def planfix_create_prodaction(order_pf_id: int, prodaction_pf_id: int, price: int, prodaction_id: int):

    url = f"{pf_url_rest}/task/{order_pf_id}"

    payload = {
        "template": {
            "id": 113 # Заказ: Новый заказ
        },
        "customFieldData": [
            {
            "field": {
                "id": 5624 # Новая готовая продукция
            },
            "value": {
                "id": prodaction_pf_id
            }
            },
            {
            "field": {
                "id": 5484 # СОХРАНИТЬ
            },
            "value": "true"
            },
            {
            "field": {
                "id": 5594 # Цена индив, RUB
            },
            "value": price
            },
            {
            "field": {
                "id": 12114 # Бронирование для проброски поля prodaction_id
            },
            "value": prodaction_id
            }
        ]
        }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {pf_token}"
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    return data



####################### CREATE CONTACT (PLANFIX) ####################################

async def planfix_create_contact(telegram_id: int, username: str, first_name: str, last_name: str):

    url = f"{pf_url_rest}/contact/"

    payload = {
        "template": {
            "id": 3071 # Шаблон контакта (OLEDBot)
        },
        "name": first_name,
        "lastname": last_name,
        "Telegram": telegram_id,
        "customFieldData": [
            {
            "field": {
                "id": 12144 # Username
            },
            "value": {
                "id": username
            }
            },
            {
            "field": {
                "id": 131 # Telegram
            },
            "value": telegram_id
            },
            # {
            # "field": {
            #     "id": 12114 # Бронирование для проброски поля prodaction_id
            # },
            # "value": prodaction_id
            # }
        ]
        }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {pf_token}"
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    return data
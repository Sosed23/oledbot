import asyncio
import requests
import sys
import aiohttp
import logging
from bot.config import pf_token, pf_url_rest

sys.stdout.reconfigure(encoding='utf-8')

# Настройка логирования
logger = logging.getLogger(__name__)


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



####################### CREATE CONTACT (PLANFIX) ####################################

async def planfix_create_contact(telegram_id: int, username: str, first_name: str, last_name: str):

    url = f"{pf_url_rest}/contact/"

    payload = {
        "template": {
            "id": 3071 # Шаблон контакта (OLEDBot)
        },
        "name": first_name,
        "lastname": last_name,
        "midname": telegram_id,
        "customFieldData": [
            {
            "field": {
                "id": 12144 # Username
            },
            "value": username
            },
            {
            "field": {
                "id": 12146 # Telegram_id
            },
            "value": telegram_id
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


####################### CREATE CHAT (PLANFIX) ####################################


async def planfix_create_chat(contact_pf_id: int):

    url = f"{pf_url_rest}/task/"

    payload = {
        "template": {
            "id": 262731 # Чат OLEDBot
        },
          "counterparty": {
            "id": contact_pf_id
        },
        # "customFieldData": [
        #     {
        #     "field": {
        #         "id": 5624 # Новая готовая продукция
        #     },
        #     "value": prodaction_pf_id
        #     }
        # ]
        }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {pf_token}"
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    return data


####################### ADD INCOMING COMMENT TO CHAT (PLANFIX) ####################################


async def add_incoming_comment_to_chat(chat_pf_id: int, comment: str, contact_pf_id: int):

    url = f"{pf_url_rest}/task/{chat_pf_id}/comments"

    payload = {
        "description": comment,
          "owner": {
            "id": f"contact:{contact_pf_id}"
        }
        }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {pf_token}"
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    return data


####################### ADD OUTGOING COMMENT TO CHAT (PLANFIX) ####################################

async def add_outgoing_comment_to_chat(chat_pf_id: int, comment: str):

    url = f"{pf_url_rest}/task/{chat_pf_id}/comments"

    payload = {
        "description": comment,
          "owner": {
            "id": "contact:3077"
        }
        }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {pf_token}"
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    return data


####################### PRICE RE-GLUING (FILTER) ####################################

async def planfix_price_re_gluing(model_id: int):

    url = f"{pf_url_rest}/directory/1430/entry/list"

    payload = {
        "offset": 0,
        "pageSize": 10,
        "fields": "name,key,3780,3782,3784,3792",   # 3780 (Цена разборки/сборки); 3782 (Цена переклейки); 
        "filterId": 104410,                                            # 3784 (Цена замены подсветки/тача); 3792 (Цена замены крышки);
        "filters": [
            {
            "type": 6114,
            "field": 4308, # Совместимость моделей
            "operator": "equal",
            "value": model_id
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


####################### BASIC NOMENCLATURE DISPLAY and BACK COVER (FILTER) ####################################

async def planfix_basic_nomenclature_re_gluing(model_id: int, filter_id: int):

    url = f"{pf_url_rest}/directory/1442/entry/list"

    payload = {
        "offset": 0,
        "pageSize": 10,
        "fields": "3884,name,key,3902,3906,3892",   # 3884 (Название); 3902 (Прайс-лист); 3906 (Карточка основной номенклатуры);
        "filterId": filter_id,                      # 3892 (Цвет)
        "filters": [
            {
            "type": 6114,
            "field": 3888, # Совместимость моделей
            "operator": "equal",
            "value": model_id
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


####################### PRICE BASIC NOMENCLATURE RE-GLUING (FILTER) ####################################

async def  planfix_price_basic_nomenclature_re_gluing(model_id: int, pricelist_key: int):

    url = f"{pf_url_rest}/directory/1430/entry/{pricelist_key}"

    payload = {
        "offset": 0,
        "pageSize": 10,
        "fields": "name,key,3782,3784",  # 3780 (Цена разборки/сборки); 3782 (Цена переклейки);
        "filterId": 104410,                         # 3784 (Цена замены подсветки/тача); 
        "filters": [
            {
            "type": 6114,
            "field": 4308, # Совместимость моделей
            "operator": "equal",
            "value": model_id
            }
        ]
        }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {pf_token}"
    }

    response = requests.get(url, json=payload, headers=headers)
    data = response.json()

    return data


####################### PRICE BASIC BACK COVER (FILTER) ####################################

async def planfix_price_basic_back_cover(model_id: int, pricelist_key: int):

    url = f"{pf_url_rest}/directory/1430/entry/{pricelist_key}"

    payload = {
        "offset": 0,
        "pageSize": 10,
        "fields": "name,key,3792",   # 3792 (Цена замены крышки); 3780 (Цена разборки/сборки);
        "filterId": 104410,                                            
        "filters": [
            {
            "type": 6114,
            "field": 4308, # Совместимость моделей
            "operator": "equal",
            "value": model_id
            }
        ]
        }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {pf_token}"
    }

    response = requests.get(url, json=payload, headers=headers)
    data = response.json()

    return data


####################### BACK COVER (FILTER) ####################################

async def planfix_back_cover_filter(model_id: str, operation: str):

    url = f"{pf_url_rest}/task/list"

    payload = {
        "offset": 0,
        "pageSize": 100,
        "filterId": "104384",
        "filters": [
            {
                "type": 107,
                "field": 5556, # Модель
                "operator": "equal",
                "value": model_id
            }
        ],
        "fields": "id,5556,"
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {pf_token}"
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    return data


####################### BASIC BACK COVER CART (FILTER) ####################################

async def planfix_basic_back_cover_cart(task_id: int, filter_id: int):

    url = f"{pf_url_rest}/directory/1442/entry/list"

    payload = {
        "offset": 0,
        "pageSize": 10,
        "fields": "3884,name,key,3902,3906,3892",   # 3884 (Название); 3902 (Прайс-лист); 3906 (Карточка основной номенклатуры);
        "filterId": filter_id,                      # 3892 (Цвет)
        "filters": [
            {
            "type": 6115,
            "field": 3906, # Карточка основной номенклатуры
            "operator": "equal",
            "value": task_id
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


####################### PRICE ASSEMBLY BASIC BACK COVER (FILTER) ####################################

async def planfix_price_assembly_basic_back_cover(model_id: int):

    url = f"{pf_url_rest}/directory/1430/entry/list"

    payload = {
        "offset": 0,
        "pageSize": 10,
        "fields": "name,key,3780",   # 3780 (Цена разборки/сборки);
        "filterId": 104410,                                            
        "filters": [
            {
            "type": 6114,
            "field": 4308, # Совместимость моделей
            "operator": "equal",
            "value": model_id
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


###### ДОБАВЛЕНИЕ ФОТО БИТИКА В ПЛАНФИКС ###############################

async def upload_files_to_planfix(photo_files: list[bytes], filename_prefix: str = "photo") -> list[int]:
    """
    Загружает несколько файлов в Planfix и возвращает список их fileId.
    
    Args:
        photo_files (list[bytes]): Список байтов файлов фотографий.
        filename_prefix (str): Префикс для имени файла (по умолчанию "photo").
    
    Returns:
        list[int]: Список fileId загруженных файлов.
    """
    url_upload = f"{pf_url_rest}/file/"
    headers = {
        "Authorization": f"Bearer {pf_token}"
    }
    
    file_ids = []
    for i, photo_file in enumerate(photo_files):
        filename = f"{filename_prefix}_{i+1}.jpg"
        files = {
            "file": (filename, photo_file, "image/jpeg")
        }
        
        try:
            response = requests.post(url_upload, headers=headers, files=files)
            response.raise_for_status()
            data = response.json()
            file_id = data.get("id")
            if not file_id:
                logger.error(f"Не удалось получить fileId для файла {filename} после загрузки в Planfix")
                continue
            logger.info(f"Файл {filename} успешно загружен в Planfix, fileId: {file_id}")
            file_ids.append(file_id)
        except Exception as e:
            logger.error(f"Ошибка при загрузке файла {filename} в Planfix: {e}")
            continue

    return file_ids

async def upload_photo_to_planfix(chat_pf_id: int, photo_files: list[bytes]) -> bool:
    """
    Загружает несколько фото в Planfix и прикрепляет их к одному комментарию в задаче.
    
    Args:
        chat_pf_id (int): ID чата/задачи в Planfix.
        photo_files (list[bytes]): Список байтов файлов фотографий.
    
    Returns:
        bool: True, если загрузка и прикрепление успешны, False в противном случае.
    """
    # Шаг 1: Загружаем все файлы в Planfix
    file_ids = await upload_files_to_planfix(photo_files)
    if not file_ids:
        logger.error("Не удалось загрузить ни один файл в Planfix")
        return False

    # Шаг 2: Создаём один комментарий с несколькими файлами
    url_comment = f"{pf_url_rest}/task/{chat_pf_id}/comments"
    payload = {
        "description": f"Добавлено {len(file_ids)} фото битика",
        "owner": {
            "id": "contact:3077"  # Тот же owner, что в add_outgoing_comment_to_chat
        },
        "files": [{"id": file_id} for file_id in file_ids]
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {pf_token}"
    }
    
    try:
        response = requests.post(url_comment, json=payload, headers=headers)
        response.raise_for_status()
        logger.info(f"{len(file_ids)} фото успешно прикреплены к задаче {chat_pf_id} в Planfix в одном комментарии")
        return True
    except Exception as e:
        logger.error(f"Ошибка при прикреплении фото к задаче {chat_pf_id} в Planfix: {e}")
        return False


####################### KEY CRASH DISPLAY PLANFIX (FILTER) ####################################

async def planfix_price_assembly_basic_back_cover(model_id: int):

    url = f"{pf_url_rest}/directory/1432/entry/list"

    payload = {
        "offset": 0,
        "pageSize": 10,
        "fields": "name,key",   # 3780 (Цена разборки/сборки);                                          
        "filters": [
            {
            "type": 6114,
            "field": 3798, # Совместимость моделей
            "operator": "equal",
            "value": model_id
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


####################### STOCK BALANCE (FILTER) ####################################

async def planfix_stock_balance_spare_parts_filter(model_id: str):

    url = f"{pf_url_rest}/task/list"

    payload = {
        "offset": 0,
        "pageSize": 10,
        "filterId": "104398",       # фильтр задач "All stock balance: spare parts"
        "filters": [
            {
                "type": 107,
                "field": 5556,      # Модель
                "operator": "equal",
                "value": model_id
            }
        ],
        "fields": "id,5512,12126,5718,5722"     # 5512 (Запчасть); 12126 (Price); 5718 (Цена закупки, RUB); 5722 (Св. остаток);
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {pf_token}"
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    return data
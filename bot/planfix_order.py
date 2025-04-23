import asyncio
import requests
import sys
import aiohttp
from bot.config import pf_token, pf_url_rest

sys.stdout.reconfigure(encoding='utf-8')


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
                "id": 1
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


####################### CREATE PRODACTION - 4 (PLANFIX) ####################################

async def planfix_create_order_prodaction_4(order_pf_id: int, prodaction_pf_id: int, price: int, prodaction_id: int):

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


####################### CREATE PRODACTION - 6 (PLANFIX) ####################################

async def planfix_create_order_back_cover_6(order_pf_id: int, back_cover_pf_id: int, price: int):

    url = f"{pf_url_rest}/task/{order_pf_id}"

    payload = {
        "template": {
            "id": 117 # Заказ: Замена крышки
        },
        "customFieldData": [
            {
            "field": {
                "id": 5650 # Задняя крышка
            },
            "value": {
                "id": back_cover_pf_id
            }
            },
            {
            "field": {
                "id": 5594 # Цена индив, RUB
            },
            "value": price
            },
            {
            "field": {
                "id": 5564 # Исполнитель на производстве (справочник)
            },
            "value": {
                "id": 9 # Демо производство (исполнитель)
            }
            },
            {
            "field": {
                "id": 5484 # СОХРАНИТЬ
            },
            "value": "true"
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
import asyncio
import requests
import sys
from bot.config import pf_token, pf_url_rest

sys.stdout.reconfigure(encoding='utf-8')

url = f"{pf_url_rest}/task/list"

payload = {
    "offset": 0,
    "pageSize": 50,
    "filterId": "104380",
    "fields": "id,12116,5542,6640,6282,12140"
}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {pf_token}"
}


async def planfix_stock_balance(query=None):
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    all_balance_tasks = data['tasks']
    result = []
    unique_devices = set()  # Создаем множество для уникальных значений device
    unique_brands = set()

    for task in all_balance_tasks:
        id_product = task['id']
        stock_balance = None
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


async def main():
    data = await planfix_stock_balance()
    print(data)

asyncio.run(main())


####################### VERSION 1 ####################################

# sys.stdout.reconfigure(encoding='utf-8')

# # URL из изображения
# url = f"{pf_url_rest}/task/list"


# headers = {
#     "Content-Type": "application/json",
#     "Authorization": f"Bearer {pf_token}"
# }


# # Функция для получения задач с определённым offset
# def fetch_tasks(offset):
#     payload = {
#         "offset": offset,
#         "pageSize": 100,
#         "filterId": "104380",
#         "filters": [
#             {
#                 "type": 51,
#                 "operator": "equal",
#                 "value": 105
#             }
#         ],
#         "fields": "id,name,12116,5542"
#     }
#     response = requests.post(url, json=payload, headers=headers)
#     if response.status_code == 200:
#         return response.json()
#     else:
#         print(f"Ошибка при запросе: {response.status_code}")
#         return None


# # Перебор страниц с задачами
# offset = 0
# all_tasks = []

# while True:
#     data = fetch_tasks(offset)

#     if not data or not data.get('tasks'):
#         break  # Если данных нет, заканчиваем цикл

#     # # Фильтрация задач, где поле с id=12116 имеет значение больше 0
#     # tasks_with_value_gt_zero = [
#     #     task for task in data['tasks']
#     #     if any(
#     #         field['field']['id'] == 12116 and field['value'] > 0
#     #         for field in task['customFieldData']
#     #     )
#     # ]

#     all_tasks.extend(data['tasks'])

#     # Если количество задач меньше pageSize, это последняя страница
#     if len(data['tasks']) < 100:
#         break

#     # Увеличиваем offset для следующего запроса
#     offset += 100

# # print(all_tasks.__len__())
# print(len(all_tasks))

# # Вывод отфильтрованных задач
# for task in all_tasks:
#     print(task)


####################### VERSION 3 ####################################


# # Функция для получения задач с определённым offset

# def fetch_tasks(offset):
#     payload = {
#         "offset": offset,
#         "pageSize": 100,
#         "filterId": "44896",
#         "filters": [
#             {
#                 "type": 51,
#                 "operator": "equal",
#                 "value": 105
#             }
#         ],
#         "fields": "id,name,12116"
#     }
#     response = requests.post(url, json=payload, headers=headers)
#     if response.status_code == 200:
#         return response.json()
#     else:
#         print(f"Ошибка при запросе: {response.status_code}")
#         return None


# # Перебор страниц с задачами
# offset = 0
# all_tasks = []

# while True:
#     data = fetch_tasks(offset)

#     if not data or not data.get('tasks'):
#         break  # Если данных нет, заканчиваем цикл

#     tasks_with_value_gt_zero = [
#         task for task in data['tasks']
#         if any(field['value'] > 0 for field in task['customFieldData'])
#     ]

#     all_tasks.extend(tasks_with_value_gt_zero)

#     # Если количество задач меньше pageSize, это последняя страница
#     if len(data['tasks']) < 100:
#         break

#     # Увеличиваем offset для следующего запроса
#     offset += 100

# print(all_tasks.__len__())

# # Вывод отфильтрованных задач
# for task in all_tasks:
#     print(task)

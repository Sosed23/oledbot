import requests
import sys
from bot.config import pf_token, pf_url_rest


sys.stdout.reconfigure(encoding='utf-8')


####################### VERSION 2 ####################################

url = f"{pf_url_rest}/task/list"

payload = {
    "offset": 0,
    "pageSize": 2,
    "filterId": "104380",
    # "filters": [
    #     {
    #         "type": 51,
    #         "operator": "equal",
    #         "value": 105
    #     }
    # ],
    "fields": "id,12116,5542"
}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {pf_token}"
}


def planfix_stock_balance():
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    # print(len(data['tasks']))
    # print(data)

    return data


planfix_stock_balance()

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

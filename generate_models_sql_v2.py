import json

# Данные из таблиц (полученные через MCP сервер)
devices = {
    "Смартфон": 1,
    "Планшет": 2,
    "Смарт часы": 3
}

brands = {
    "Samsung": 1,
    "Apple": 2
}

# Данные из таблицы series (полученные через MCP сервер)
series_data = [
    {"id": 1, "device_id": 1, "brand_id": 1, "name": "Galaxy S"},
    {"id": 2, "device_id": 1, "brand_id": 1, "name": "Galaxy Note"},
    {"id": 3, "device_id": 1, "brand_id": 1, "name": "Galaxy Z"},
    {"id": 4, "device_id": 1, "brand_id": 1, "name": "Galaxy A"},
    {"id": 5, "device_id": 1, "brand_id": 1, "name": "Galaxy M"},
    {"id": 6, "device_id": 1, "brand_id": 1, "name": "Galaxy J"},
    {"id": 7, "device_id": 1, "brand_id": 2, "name": "iPhone"},
    {"id": 8, "device_id": 1, "brand_id": 2, "name": "iPhone SE"},
    {"id": 9, "device_id": 1, "brand_id": 2, "name": "iPhone mini"},
    {"id": 10, "device_id": 1, "brand_id": 2, "name": "iPhone Plus"},
    {"id": 11, "device_id": 1, "brand_id": 2, "name": "iPhone Pro"},
    {"id": 12, "device_id": 1, "brand_id": 2, "name": "iPhone Pro Max"},
    {"id": 13, "device_id": 2, "brand_id": 1, "name": "Galaxy Tab S"},
    {"id": 14, "device_id": 2, "brand_id": 1, "name": "Galaxy Tab A"},
    {"id": 15, "device_id": 2, "brand_id": 1, "name": "Galaxy Tab FE"},
    {"id": 16, "device_id": 2, "brand_id": 1, "name": "Galaxy Tab Active"},
    {"id": 17, "device_id": 2, "brand_id": 2, "name": "iPad"},
    {"id": 18, "device_id": 2, "brand_id": 2, "name": "iPad mini"},
    {"id": 19, "device_id": 2, "brand_id": 2, "name": "iPad Air"},
    {"id": 20, "device_id": 2, "brand_id": 2, "name": "iPad Pro"},
    {"id": 21, "device_id": 3, "brand_id": 1, "name": "Galaxy Watch"},
    {"id": 22, "device_id": 3, "brand_id": 1, "name": "Galaxy Fit"},
    {"id": 23, "device_id": 3, "brand_id": 2, "name": "Apple Watch Series"},
    {"id": 24, "device_id": 3, "brand_id": 2, "name": "Apple Watch SE"},
    {"id": 25, "device_id": 3, "brand_id": 2, "name": "Apple Watch Ultra"}
]

# Создаем словарь для быстрого поиска series_id по device_id, brand_id и name
series = {}
for s in series_data:
    key = (s["device_id"], s["brand_id"], s["name"])
    series[key] = s["id"]

# Функция для генерации SQL-запросов вставки
def generate_insert_queries(models_data):
    queries = []
    
    # Разобьем данные на пакеты по 50 записей для удобства выполнения
    batch_size = 50
    for i in range(0, len(models_data), batch_size):
        batch = models_data[i:i + batch_size]
        values = []
        
        for model in batch:
            device_name = model["device"]
            brand_name = model["brand"]
            series_name = model["series"]
            
            device_id = devices.get(device_name)
            brand_id = brands.get(brand_name)
            series_id = series.get((device_id, brand_id, series_name))
            name = model["name"]
            model_id = model["model_id"]
            
            # Проверим, что все идентификаторы найдены
            if device_id and brand_id and series_id:
                # Обработка NULL значений для model_id
                model_id_str = 'NULL' if model_id is None else str(model_id)
                # Экранируем одинарные кавычки в названии модели
                escaped_name = name.replace("'", "''")
                values.append(f"({device_id}, {brand_id}, {series_id}, '{escaped_name}', {model_id_str})")
            else:
                print(f"Не удалось найти идентификаторы для модели: {model}")
        
        if values:
            # Создаем SQL-запрос для пакета
            values_str = ", ".join(values)
            query = f"INSERT INTO models_new (device_id, brand_id, series_id, name, model_id) VALUES {values_str};"
            queries.append(query)
    
    return queries

# Основная функция
def main():
    # Читаем данные из JSON файла
    with open('bot/stocks/new_filters.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    models_data = data["models"]
    
    # Генерируем SQL-запросы
    queries = generate_insert_queries(models_data)
    
    # Сохраняем запросы в файл
    with open('insert_models_queries.sql', 'w', encoding='utf-8') as f:
        f.write(f"-- Сгенерировано {len(queries)} пакетов запросов для вставки {len(models_data)} моделей\n")
        f.write(f"-- Первый пакет содержит {min(50, len(models_data))} записей\n\n")
        
        for i, query in enumerate(queries):
            f.write(f"-- Пакет {i+1}\n")
            f.write(f"{query}\n\n")
    
    # Выводим информацию о сгенерированных запросах
    print(f"Сгенерировано {len(queries)} пакетов запросов для вставки {len(models_data)} моделей")
    print("Запросы сохранены в файл 'insert_models_queries.sql'")

if __name__ == "__main__":
    main()
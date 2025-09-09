import json

# Справочные данные (идентификаторы из таблиц devices, brands и series)
devices = {
    "Смартфон": 1,
    "Планшет": 2,
    "Смарт часы": 3
}

brands = {
    "Samsung": 1,
    "Apple": 2
}

series = {
    ("Смартфон", "Samsung", "Galaxy S"): 1,
    ("Смартфон", "Samsung", "Galaxy Note"): 2,
    ("Смартфон", "Samsung", "Galaxy Z"): 3,
    ("Смартфон", "Samsung", "Galaxy A"): 4,
    ("Смартфон", "Samsung", "Galaxy M"): 5,
    ("Смартфон", "Samsung", "Galaxy J"): 6,
    ("Смартфон", "Apple", "iPhone"): 7,
    ("Смартфон", "Apple", "iPhone SE"): 8,
    ("Смартфон", "Apple", "iPhone mini"): 9,
    ("Смартфон", "Apple", "iPhone Plus"): 10,
    ("Смартфон", "Apple", "iPhone Pro"): 11,
    ("Смартфон", "Apple", "iPhone Pro Max"): 12,
    ("Планшет", "Samsung", "Galaxy Tab S"): 13,
    ("Планшет", "Samsung", "Galaxy Tab A"): 14,
    ("Планшет", "Samsung", "Galaxy Tab FE"): 15,
    ("Планшет", "Samsung", "Galaxy Tab Active"): 16,
    ("Планшет", "Apple", "iPad"): 17,
    ("Планшет", "Apple", "iPad mini"): 18,
    ("Планшет", "Apple", "iPad Air"): 19,
    ("Планшет", "Apple", "iPad Pro"): 20,
    ("Смарт часы", "Samsung", "Galaxy Watch"): 21,
    ("Смарт часы", "Samsung", "Galaxy Fit"): 22,
    ("Смарт часы", "Apple", "Apple Watch Series"): 23,
    ("Смарт часы", "Apple", "Apple Watch SE"): 24,
    ("Смарт часы", "Apple", "Apple Watch Ultra"): 25
}

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
            series_id = series.get((device_name, brand_name, series_name))
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
    
    # Выводим информацию о сгенерированных запросах
    print(f"-- Сгенерировано {len(queries)} пакетов запросов для вставки {len(models_data)} моделей")
    print(f"-- Первый пакет содержит {min(50, len(models_data))} записей")
    
    # Выводим запросы
    for i, query in enumerate(queries):
        print(f"\n-- Пакет {i+1}")
        print(query)
        
        # Ограничиваем вывод первыми 5 пакетами для удобства просмотра
        if i >= 4:
            remaining = len(queries) - (i + 1)
            if remaining > 0:
                print(f"\n-- Еще {remaining} пакетов опущено для краткости")
                print("-- Чтобы увидеть все пакеты, измените лимит в скрипте")
            break

if __name__ == "__main__":
    main()
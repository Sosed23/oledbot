import json
import psycopg2
from psycopg2.extras import execute_values

# Функция для подключения к базе данных
def get_db_connection():
    # В реальном приложении здесь должны быть правильные параметры подключения
    # Для этого примера мы просто создадим заглушку
    pass

# Функция для получения данных из таблиц (заглушки)
def get_reference_data():
    # В реальном приложении здесь будут SQL-запросы к базе данных
    # Для этого примера мы используем данные, которые уже получили ранее
    
    devices = {
        "Смартфон": 1,
        "Планшет": 2,
        "Смарт часы": 3
    }
    
    brands = {
        "Samsung": 1,
        "Apple": 2
    }
    
    # Для серий мы создадим словарь на основе данных, которые уже получили
    series = {
        (1, 1, "Galaxy S"): 1,
        (1, 1, "Galaxy Note"): 2,
        (1, 1, "Galaxy Z"): 3,
        (1, 1, "Galaxy A"): 4,
        (1, 1, "Galaxy M"): 5,
        (1, 1, "Galaxy J"): 6,
        (1, 2, "iPhone"): 7,
        (1, 2, "iPhone SE"): 8,
        (1, 2, "iPhone mini"): 9,
        (1, 2, "iPhone Plus"): 10,
        (1, 2, "iPhone Pro"): 11,
        (1, 2, "iPhone Pro Max"): 12,
        (2, 1, "Galaxy Tab S"): 13,
        (2, 1, "Galaxy Tab A"): 14,
        (2, 1, "Galaxy Tab FE"): 15,
        (2, 1, "Galaxy Tab Active"): 16,
        (2, 2, "iPad"): 17,
        (2, 2, "iPad mini"): 18,
        (2, 2, "iPad Air"): 19,
        (2, 2, "iPad Pro"): 20,
        (3, 1, "Galaxy Watch"): 21,
        (3, 1, "Galaxy Fit"): 22,
        (3, 2, "Apple Watch Series"): 23,
        (3, 2, "Apple Watch SE"): 24,
        (3, 2, "Apple Watch Ultra"): 25
    }
    
    return devices, brands, series

# Функция для генерации SQL-запросов вставки
def generate_insert_queries(models_data, devices, brands, series):
    queries = []
    
    # Разобьем данные на пакеты по 100 записей для эффективности
    batch_size = 10
    for i in range(0, len(models_data), batch_size):
        batch = models_data[i:i + batch_size]
        values = []
        
        for model in batch:
            device_id = devices.get(model["device"])
            brand_id = brands.get(model["brand"])
            series_id = series.get((devices.get(model["device"]), brands.get(model["brand"]), model["series"]))
            name = model["name"]
            model_id = model["model_id"]
            
            # Проверим, что все идентификаторы найдены
            if device_id and brand_id and series_id:
                values.append((device_id, brand_id, series_id, name, model_id))
            else:
                print(f"Не удалось найти идентификаторы для модели: {model}")
        
        if values:
            # Создаем SQL-запрос для пакета
            query = "INSERT INTO models_new (device_id, brand_id, series_id, name, model_id) VALUES %s"
            queries.append((query, values))
    
    return queries

# Основная функция
def main():
    # Читаем данные из JSON файла
    with open('bot/stocks/new_filters.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    models_data = data["models"]
    
    # Получаем справочные данные
    devices, brands, series = get_reference_data()
    
    # Генерируем SQL-запросы
    queries = generate_insert_queries(models_data, devices, brands, series)
    
    # Выводим информацию о сгенерированных запросах
    print(f"Сгенерировано {len(queries)} пакетов запросов для вставки {len(models_data)} моделей")
    
    # В реальном приложении здесь будут выполнены запросы к базе данных
    # Например:
    # conn = get_db_connection()
    # cur = conn.cursor()
    # for query, values in queries:
    #     execute_values(cur, query, values)
    # conn.commit()
    # cur.close()
    # conn.close()
    
    # Для демонстрации выведем первый пакет запросов
    if queries:
        query, values = queries[0]
        print("\nПример первого пакета запросов:")
        print(f"Запрос: {query}")
        print(f"Первые 3 значения: {values[:3]}")

if __name__ == "__main__":
    main()
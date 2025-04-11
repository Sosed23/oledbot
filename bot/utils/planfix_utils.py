from loguru import logger

def extract_price_from_data(data):
    """
    Извлекает цену из данных Planfix, проверяя поле 'Цена, RUB' в customFieldData.
    Возвращает None, если цена не найдена.
    """
    try:
        tasks = data.get("tasks", [])
        for task in tasks:
            for field_data in task.get("customFieldData", []):
                field_name = field_data.get("field", {}).get("name", "")
                if field_name == "Цена, RUB":
                    return field_data.get("stringValue") or str(field_data.get("value", ""))
    except Exception as e:
        logger.error(f"Ошибка при извлечении цены: {e}")
    return None

def extract_balance_from_data(data):
    """
    Извлекает баланс (поле 'Приход') из данных Planfix.
    Возвращает None, если баланс не найден.
    """
    try:
        tasks = data.get("tasks", [])
        for task in tasks:
            for field_data in task.get("customFieldData", []):
                field_name = field_data.get("field", {}).get("name", "")
                if field_name == "Приход":
                    return field_data.get("stringValue") or str(field_data.get("value", ""))
    except Exception as e:
        logger.error(f"Ошибка при извлечении баланса: {e}")
    return None
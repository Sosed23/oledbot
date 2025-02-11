# Используем официальный образ Python 3.13
FROM python:3.13 

# Устанавливаем рабочую директорию
WORKDIR /code

# Копируем файл с зависимостями
COPY ./requirements.txt /code/requirements.txt

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r /code/requirements.txt

# Копируем все файлы проекта
COPY ./ /code/

# Команда для запуска бота
CMD ["python", "-m", "bot.main"]

FROM python:3.13.3

WORKDIR /app


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . .

# Запускаем бота
CMD ["python", "bot.py"]
FROM python:3.12-slim

WORKDIR /app

# Устанавливаем системные утилиты (если build.sh использует bash или curl/wget)
RUN apt-get update && apt-get install -y bash && rm -rf /var/lib/apt/lists/*

COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Делаем скрипт исполняемым
RUN chmod +x src/build.sh

# Указываем команду по умолчанию для запуска вашего sh-скрипта
CMD ["app/src/build.sh x86_64 app/src/app/main.py"]

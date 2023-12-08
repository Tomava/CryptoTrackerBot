FROM python:3.11-buster

# Uncomment everything below if not running rootless Docker

# RUN useradd -u 1000 telegram
# RUN mkdir /home/telegram
# RUN chown -R telegram /home/telegram
#USER telegram

WORKDIR /app

COPY *.py ./
COPY requirements.txt ./
COPY .env ./

RUN pip3.11 install -r requirements.txt

CMD ["python3", "CryptoTelegramBot.py"]
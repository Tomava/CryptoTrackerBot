FROM python:3.11-buster

RUN useradd -u 1000 telegram
RUN mkdir /home/telegram
RUN chown -R telegram /home/telegram

WORKDIR /home/telegram

COPY *.py ./
COPY requirements.txt ./

USER telegram

RUN pip3.11 install -r requirements.txt

CMD ["python3", "CryptoTelegramBot.py"]
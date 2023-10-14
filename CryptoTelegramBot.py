import os
# import memory_profiler
import telebot
import urllib.request
import json
import io
from datetime import datetime
import matplotlib.pyplot as plt
import time
import gc
from PIL import Image
import math
from Config import *


# def create_ticks(all_coords, round_to):
#     # Create ticks
#     ticks = []
#     min_value = min(all_coords)
#     max_value = max(all_coords)
#     for i in range(math.floor(min_value / round_to) * round_to, math.ceil(max_value / round_to + 1) * round_to, round_to):
#         ticks.append(i)
#     return ticks

def get_from_file(file_name):
    """
    Gets favourites from a file
    :param file_name str
    :return: dict
    """
    if not os.path.exists(file_name):
        with open(file_name, "w", encoding="utf-8") as file:
            json.dump({}, file)
    with open(file_name, "r", encoding="utf-8") as file:
        obj = json.load(file)
    return obj


def get_valid_names():
    """
    Fetches valid crypto_names
    :return: dict
    """
    url = "https://api.coingecko.com/api/v3/coins/list?include_platform=false"
    try:
        with urllib.request.urlopen(url) as site:
            temp_data = json.loads(site.read())
        ids = []
        for value in temp_data:
            ids.append(value.get("id"))
    # Backup
    except:
        with open(VALID_NAMES, "r", encoding="utf-8") as file:
            ids = file.readline().split(", ")
    ids = set(ids)
    return ids


def get_arguments(message):
    """
    Parse arguments from message
    :param message: Message
    :return: list
    """
    arguments = message.text.split()
    return arguments[1:]


class CryptoTelegramBot:
    def __init__(self):
        self.__favourite_crypto_names = get_from_file(FAVOURITES_FILE)
        self.__min_alerts = get_from_file(MIN_ALERT_FILE)
        self.__max_alerts = get_from_file(MAX_ALERT_FILE)
        if not os.path.exists(ERROR_NOTIFICATIONS_FILE):
            with open(ERROR_NOTIFICATIONS_FILE, "w", encoding="utf-8") as file:
                json.dump([], file)
        with open(ERROR_NOTIFICATIONS_FILE, "r", encoding="utf-8") as file:
            self.__error_notifications = json.load(file)
        self.authorized_users = AUTHORIZED_USERS
        self.__bot = telebot.TeleBot(TELEGRAM_BOT_API)
        self.__valid_crypto_names = get_valid_names()
        # Start listening to the telegram bot and whenever a message is  received, the handle function will be called.
        self.bot_messages()
        self.__bot.infinity_polling()
        print('Listening....')
        self.handle_alerts()
        # while 1:
        #     time.sleep(900)

    def is_user_authorized(self, func):
        def wrapped(message):
            if str(message.from_user.id) in self.authorized_users:
                func(message)
            else:
                print(f"User {message.from_user.id} not authorized!")
        return wrapped

    def save_favourites(self):
        """
        Saves favourites to a file
        :return: nothing
        """
        with open(FAVOURITES_FILE, "w", encoding="utf-8") as file:
            json.dump(self.__favourite_crypto_names, file)

    def save_error_notifications(self):
        """
        Saves favourites to a file
        :return: nothing
        """
        with open(ERROR_NOTIFICATIONS_FILE, "w", encoding="utf-8") as file:
            json.dump(self.__error_notifications, file)

    def make_graph(self, title, data):
        """
        Crafts a graph
        :param title: str
        :param data: dict
        :return: Plot figure
        """
        given_fig, given_plot = plt.subplots(num=title)
        # Timestamps are in milliseconds
        date_objects = [datetime.fromtimestamp(timestamp / 1000) for timestamp in data.keys()]
        given_plot.plot(date_objects, data.values())

        given_plot.grid()
        # y_ticks = create_ticks(data.values(), 1000)
        # x_ticks = create_ticks(data.keys(), 1000)
        # given_plot.set_yticks(y_ticks)
        # given_plot.set_xticks(x_ticks)
        given_plot.set_title(title)
        given_plot.set_xlabel("Time")
        given_plot.set_ylabel("Price (€)")
        given_fig.set_figwidth(10)
        given_fig.set_figheight(6)
        return given_fig

    def get_historical_data(self, crypto_name):
        """
        Gets prices
        :param crypto_name: str
        :return: list, List of plot figure
        """
        # https://api.coingecko.com/api/v3/coins/ethereum/market_chart?vs_currency=eur&days=max
        base_url = f"https://api.coingecko.com/api/v3/coins/{crypto_name}/market_chart?vs_currency=eur"
        time_frames = [90, 7, 1]
        graphs = []
        for time_frame in time_frames:
            url = f"{base_url}&days={time_frame}"
            try:
                with urllib.request.urlopen(url) as site:
                    temp_data = json.loads(site.read()).get("prices")
                    data = {}
                    for pair in temp_data:
                        timestamp = pair[0]
                        price = pair[1]
                        data[timestamp] = price
                    title = f"{crypto_name.capitalize()} ({time_frame} days)"
                    graphs.append(self.make_graph(title, data))
            except:
                print("ERROR")
        return graphs

    def get_empty_image(self, images):
        """
        Returns one image with a combined width of multiple images
        :param images: list
        :return: Image
        """
        widths, heights = zip(*(i.size for i in images))
        total_width = max(widths)
        max_height = sum(heights)
        new_im = Image.new('RGB', (total_width, max_height))
        return new_im

    def combine_vertically(self, images):
        """
        Combines images to one image vertically
        :param images: list
        :return: Image
        """
        new_im = self.get_empty_image(images)
        y_offset = 0
        for im in images:
            new_im.paste(im, (0, y_offset))
            y_offset += im.size[1]
        return new_im

    def combine_horizontally(self, images):
        """
        Combines images to one image horizontally
        :param images: list
        :return: Image
        """
        new_im = self.get_empty_image(images)
        x_offset = 0
        for im in images:
            new_im.paste(im, (x_offset, 0))
            x_offset += im.size[0]
        return new_im

    # @memory_profiler.profile()
    def get_images(self, crypto_name):
        """
        Makes images for a given crypto
        :param crypto_name: str
        :return: Image
        """
        graphs = self.get_historical_data(crypto_name)
        images_bytes = []
        for i, graph in enumerate(graphs):
            buf = io.BytesIO()
            graph.savefig(buf, format="png", bbox_inches='tight')
            buf.seek(0)
            images_bytes.append(buf.getvalue())
            # Send images separately by uncommenting line below
            # bot.sendPhoto(chat_id, buf)
        # bot.sendMediaGroup(chat_id, images)
        images = [Image.open(io.BytesIO(image_data)) for image_data in images_bytes]
        new_im = self.combine_vertically(images)
        # Clear the current axes.
        plt.cla()
        # Clear the current figure.
        plt.clf()
        # Closes all the figure windows.
        plt.close('all')
        gc.collect()
        return new_im

    def get_crypto_name(self, crypto_name):
        """
        Gets a crypto name from string
        :param crypto_name: str
        :return: str
        """
        if crypto_name in self.__favourite_crypto_names:
            crypto_name = self.__favourite_crypto_names.get(crypto_name)
        elif crypto_name not in self.__valid_crypto_names:
            return None
        return crypto_name

    def price_command(self, message):
        """
        Handles !price command
        :param message: Message
        :return: nothing
        """
        arguments = get_arguments(message)
        if len(arguments) < 1:
            self.__bot.reply_to(message, "Too few arguments!")
            return
        crypto_name = arguments[0].lower()
        images = []
        if crypto_name == "all":
            self.__bot.reply_to(message, f"Fetching all favourites.")
            for crypto_name in self.__favourite_crypto_names.values():
                images.append(self.get_images(crypto_name))
        else:
            crypto_name = self.get_crypto_name(crypto_name)
            if crypto_name is not None:
                self.__bot.reply_to(message, f"Fetching {crypto_name.capitalize()}.")
                images.append(self.get_images(crypto_name))
            else:
                self.__bot.reply_to(message, "Not a valid cryptocurrency!")
                return
        # Uncomment line below and comment the line below it to combine all photos
        # new_im = combine_horizontally(images)
        for new_im in images:
            buf = io.BytesIO()
            new_im.save(buf, "png")
            buf.seek(0)
            self.__bot.send_photo(message.chat.id, buf)

    def write_alerts_to_disk(self):
        """
        Writes alerts to disk
        :return: nothing
        """
        with open(MIN_ALERT_FILE, "w", encoding="utf-8") as file:
            json.dump(self.__min_alerts, file)
        with open(MAX_ALERT_FILE, "w", encoding="utf-8") as file:
            json.dump(self.__max_alerts, file)

    def alert_command(self, message):
        """
        Handles !alert command
        :param message: Message
        :return: nothing
        """
        arguments = get_arguments(message)
        chat_id = str(message.chat.id)
        if len(arguments) < 3:
            message = ""
            for coin_id in self.__min_alerts.get(chat_id):
                message += f"{coin_id.capitalize()}: <{self.__min_alerts.get(chat_id).get(coin_id)} €\n"
            for coin_id in self.__max_alerts.get(chat_id):
                message += f"{coin_id.capitalize()}: >{self.__max_alerts.get(chat_id).get(coin_id)} €\n"
            self.__bot.send_message(chat_id, message)
            return
        command = arguments[0]
        crypto_name = arguments[1].lower()
        amount = float(arguments[2])
        crypto_name = self.get_crypto_name(crypto_name)
        if crypto_name is None:
            self.__bot.send_messagege(chat_id, "Not a valid cryptocurrency!")
            return
        if command == "min":
            self.__min_alerts[chat_id][crypto_name] = amount
            self.__bot.send_messagege(chat_id, f"Added alert for {crypto_name.capitalize()} at <{amount} €")
            # Add empty dictionary to max_alerts to not cause error on handle_alerts
            if chat_id not in self.__max_alerts:
                self.__max_alerts[chat_id] = {}
            self.write_alerts_to_disk()
        elif command == "max":
            self.__max_alerts[chat_id][crypto_name] = amount
            self.__bot.send_messagege(chat_id, f"Added alert for {crypto_name.capitalize()} at >{amount} €")
            # Add empty dictionary to min_alerts to not cause error on handle_alerts
            if chat_id not in self.__min_alerts:
                self.__max_alerts[chat_id] = {}
            self.write_alerts_to_disk()

    def handle_alerts(self):
        """
        Handles alerts
        :return: nothing
        """

        def get_data(coin_id):
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
            try:
                with urllib.request.urlopen(url) as site:
                    current_price = json.loads(site.read()).get("market_data").get("current_price").get("eur")
                    return current_price
            except:
                print("ERROR IN ALERTS")
                return None

        while True:
            error = False
            message = ""
            for chat_id in set(self.__min_alerts.keys()).union(set(self.__max_alerts.keys())):
                chat_id = str(chat_id)
                for coin_id in set(self.__min_alerts.get(chat_id).keys()).union(set(self.__max_alerts.get(chat_id).keys())):
                    current_price = get_data(coin_id)
                    if current_price is None:
                        error = True
                        continue
                    # Check min alerts
                    if coin_id in self.__min_alerts.get(chat_id):
                        if current_price <= self.__min_alerts.get(chat_id).get(coin_id):
                            message += f"{coin_id.capitalize()} is currently at {current_price} € " \
                                       f"(<{self.__min_alerts.get(chat_id).get(coin_id)} €)\n"
                            self.__min_alerts.get(chat_id).pop(coin_id, None)
                            self.write_alerts_to_disk()
                    # Check max alert
                    if coin_id in self.__max_alerts.get(chat_id):
                        if current_price >= self.__max_alerts.get(chat_id).get(coin_id):
                            message += f"{coin_id.capitalize()} is currently at {current_price} € " \
                                       f"(>{self.__max_alerts.get(chat_id).get(coin_id)} €)\n"
                            self.__max_alerts.get(chat_id).pop(coin_id, None)
                            self.write_alerts_to_disk()
                if error and chat_id in self.__error_notifications:
                    self.__bot.send_message(chat_id, "Error while fetching current price!")
                if message != "":
                    self.__bot.send_message(chat_id, message)
            time.sleep(900)

    def help_command(self, message):
        """
        Handles !help command
        :param message: Message
        :return: nothing
        """
        chat_id = str(message.chat.id)
        message = ""
        for command in HELP_TEXT:
            message += f"<u><b>{command}</b></u>: <i>{HELP_TEXT.get(command)}</i>\n"
        self.__bot.send_message(chat_id, message, parse_mode="HTML")

    def favourite_command(self, message):
        """
        Handles !favourite command
        :param message: Message
        :return: nothing
        """
        arguments = get_arguments(message)
        chat_id = str(message.chat.id)
        if len(arguments) < 2:
            message = ""
            for short_name, full_name in self.__favourite_crypto_names.items():
                message += f"{short_name}: {full_name}\n"
            self.__bot.send_message(chat_id, message)
            return
        short_name = arguments[0].lower()
        full_name = arguments[1].lower()
        if short_name == "remove":
            if full_name in self.__favourite_crypto_names:
                self.__favourite_crypto_names.pop(full_name)
                self.__bot.send_message(chat_id, f"Remove a favourite from '{full_name}'")
                self.save_favourites()
            else:
                self.__bot.send_message(chat_id, f"That favourite is not in use!")
            return
        else:
            if short_name in self.__favourite_crypto_names or short_name in self.__valid_crypto_names:
                self.__bot.send_message(chat_id, f"That favourite is already in use!")
                return
            real_name = self.get_crypto_name(full_name)
            if real_name is None:
                self.__bot.send_message(chat_id, "Not a valid cryptocurrency!")
            else:
                self.__favourite_crypto_names[short_name] = real_name
                self.save_favourites()
                self.__bot.send_message(chat_id, f"Added a favourite for '{real_name}' as '{short_name}'")

    def error_command(self, message):
        """
        Handles !alert command
        :param message: Message
        :return: nothing
        """
        chat_id = str(message.chat.id)
        if chat_id in self.__error_notifications:
            self.__error_notifications.remove(chat_id)
            self.__bot.send_message(chat_id, "Removed this chat from error notifications")
        else:
            self.__error_notifications.append(chat_id)
            self.__bot.send_message(chat_id, "Added this chat to error notifications")
        self.save_error_notifications()

    def bot_messages(self):
        print("Message received!")

        @self.__bot.message_handler(commands=["p"])
        @self.is_user_authorized
        def price_handler(message):
            self.price_command(message)

        @self.__bot.message_handler(commands=["a"])
        @self.is_user_authorized
        def alert_handler(message):
            self.alert_command(message)

        @self.__bot.message_handler(commands=["h"])
        @self.is_user_authorized
        def help_handler(message):
            self.help_command(message)

        @self.__bot.message_handler(commands=["f"])
        @self.is_user_authorized
        def favourite_handler(message):
            self.favourite_command(message)

        @self.__bot.message_handler(commands=["e"])
        @self.is_user_authorized
        def error_handler(message):
            self.error_command(message)


def main():
    plt.switch_backend('agg')
    CryptoTelegramBot()


if __name__ == "__main__":
    main()

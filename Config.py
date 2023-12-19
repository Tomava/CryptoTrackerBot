from dotenv import load_dotenv
import os
PREFIX = "/"
HELP_TEXT = {"/p [coin_name / 'all']": "Gets graphs for a given coin",
             "/a [min / max] [coin_name] [amount]": "Adds an alert for a given coin",
             "/a": "Lists all alerts",
             "/f [short_name] [full_name]": "Adds a short version of a given full name",
             "/f": "Lists all favourites",
             "/f remove [short_name]": "Removes a favourite",
             "/e": "Toggles error notifications for this chat"}
DIRECTORY = "data"
MIN_ALERT_FILE = f"{DIRECTORY}{os.sep}min_alerts.json"
MAX_ALERT_FILE = f"{DIRECTORY}{os.sep}max_alerts.json"
ERROR_NOTIFICATIONS_FILE = f"{DIRECTORY}{os.sep}error_notifications.json"
FAVOURITES_FILE = f"{DIRECTORY}{os.sep}favourites.json"
VALID_NAMES = f"{DIRECTORY}{os.sep}valid_names.txt"
load_dotenv()
TELEGRAM_BOT_API = os.getenv('TELEGRAM_BOT_API')
AUTHORIZED_USERS = list(os.getenv("AUTHORIZED_USERS").split(" "))

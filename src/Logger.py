import logging
import datetime
import re
from logging.handlers import TimedRotatingFileHandler

OKAY = '\033[92m'
CYAN = '\033[96m'
WARNING = '\033[93m'
FAIL = '\033[91m'
MAGENTA = '\033[35m'
LIGHT_GRAY = '\033[37m'
BOLD = '\033[1m'
ENDC = '\033[0m'

class Logger:
    def __init__(self, log_filename=None):
        if log_filename is None:
            log_filename = f"log_{datetime.date.today()}.txt"
        self.log_filename = f"../data/console_logs/{log_filename}"

        # Set up the logger
        log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

        # Create a handler that rotates logs daily
        log_handler = TimedRotatingFileHandler(self.log_filename, when="midnight", interval=1, backupCount=7)
        log_handler.setFormatter(log_formatter)

        self.logger.addHandler(log_handler)

    def print_info(self, message: str, bold: bool = False, timestamp: bool = True):
        formatted_message = self.bold_and_timestamp(message, bold, timestamp)
        self.logger.info(self.remove_non_ascii(message))
        print(formatted_message)

    def print_warning(self, message: str, bold: bool = False, timestamp: bool = True):
        self.logger.warning(self.remove_non_ascii(message))
        formatted_message = self.bold_and_timestamp(f"{WARNING}{message}{ENDC}", bold, timestamp)
        print(formatted_message)

    def print_error(self, message: str, bold: bool = False, timestamp: bool = True):
        self.logger.error(self.remove_non_ascii(message))
        formatted_message = self.bold_and_timestamp(f"{FAIL}{message}{ENDC}", bold, timestamp)
        print(formatted_message)

    def print_success(self, message: str, bold: bool = False, timestamp: bool = True):
        self.logger.info(self.remove_non_ascii(message))
        formatted_message = self.bold_and_timestamp(f"{OKAY}{message}{ENDC}", bold, timestamp)
        print(formatted_message)

    def bold_and_timestamp(self, message: str, bold: bool = False, timestamp: bool = True):
        formatted_message = message
        if bold:
            formatted_message = f"{BOLD}{formatted_message}{ENDC}"
        if timestamp:
            formatted_message = f"[{self.get_timestamp()}] {formatted_message}"
        else:
            formatted_message = f"           {formatted_message}"
        return formatted_message

    def remove_non_ascii(self, input_string):
        return re.sub(r'[^\x00-\x7F]+', '', input_string)

    def get_timestamp(self):
        now = datetime.datetime.now()
        return now.strftime("%H:%M:%S")
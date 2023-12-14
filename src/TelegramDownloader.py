import os
import re
import sys
import time
import Logger
from telethon.tl import types


class TelegramDownloader:
    def __init__(self, logger, file_manager, data_analysis, download_path):
        self.logger = logger
        self.file_manager = file_manager
        self.data_analysis = data_analysis
        
        self.download_path = download_path

        self.donwload_start_time = None

        self.download_animation = [">  ", "-> ", " ->", "  -"]
    
    def extract_password(self, text):
        # Define a regular expression pattern to capture the password following "PASS:" or "Password:"
        pattern = r'(PASS:|Password:)\s*(\S+)'

        # Search for the pattern in the text
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            # Extract the captured password group (group 2)
            password = match.group(2)
            return password

        # If no password is found, return None
        return None

    async def progress(self, received, total):
        elapsed_time = time.time() - self.donwload_start_time
        download_speed_mbps = received / (elapsed_time * 1e6)  # MB/s

        progress_percentage = received / total
        progress_bar_length = 30  # Adjust the length of the progress bar
        completed_length = int(progress_percentage * progress_bar_length)

        progress_bar = "|" + "█" * completed_length + " " * (progress_bar_length - completed_length) + "|"
        
        sys.stdout.write(f"\r           {progress_bar} [{Logger.BOLD}{self.download_animation[int(received / 1e6) % 4]}{Logger.ENDC}] {progress_percentage * 100:.2f}% [{(received / 1e6):.1f}MB/{(total / 1e6):.1f}MB] @ {download_speed_mbps:.2f}MB/s")
        sys.stdout.flush()

    async def handle_message(self, event, chat_name):
        message_title = f" New message from {chat_name}! "
        self.logger.print_success(f"{message_title:{'+'}^68}", True)
        # Check if the message has a document (file) attached
        if not (event.media and isinstance(event.media, types.MessageMediaDocument)):
            self.logger.print_warning(f"Message does not contain any file.\n\n\n")
            return

        document = event.media.document

        # Check if the file has attributes
        if not document.attributes:
            self.logger.print_warning(f"Can't read file attributes from the Telegram message!\n\n\n")
            return

        file_name = document.attributes[0].file_name.lower()
        _, file_ending = os.path.splitext(file_name)

        # Check if the file has a specific extension (e.g., .zip or .rar)
        if not file_name.endswith(('.zip', '.rar')):
            self.logger.print_warning(f"Message does not contain a compatible file.\n\n\n")
            return

        password = self.extract_password(event.raw_text)

        if password and file_ending.lower() == ".zip":
            self.logger.print_warning("Unable analyze a password protected .ZIP!\n\n\n")
            return
        
        print("")
        self.logger.print_info(f"Compatible file: {Logger.CYAN}{file_name}{Logger.ENDC}", True)
        if password:
            self.logger.print_info(f"Password: {Logger.CYAN}{password}{Logger.ENDC}", True)
        file_path = os.path.join(self.download_path, file_name)

        # Download the attached file
        self.logger.print_info(f"--------------------------------------------------------------------", True, False)
        self.logger.print_info("Downloading...", False, False)
        self.donwload_start_time = time.time()
        await event.client.download_media(document, file_path, progress_callback=self.progress)
        print("")
        self.logger.print_info(f"--------------------------------------------------------------------\n", True, False)

        if file_name.endswith('.rar'):
            file_path, file_name = self.file_manager.convert_rar_to_zip(file_path, file_name, password)
            
            # Return if conversion failed
            if file_path == "" and file_path == "":
                self.logger.print_warning("Conversion from .RAR to .ZIP failed!\n\n\n")
                return

        self.data_analysis.start_scanning(file_path, file_name, True)
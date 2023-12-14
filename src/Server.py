import FileManager
import DatabaseManager
import TelegramDownloader
import TelegramPoster
import DataAnalysis
import Logger
import pyglet
import sys
import os
import time
import LocalSearchManager
import asyncio
from telethon import TelegramClient, events

class Server:
    def __init__(self):
        self.version = "1.5"

        self.logger = Logger.Logger()
        self.file_manager = FileManager.FileManager(logger=self.logger)

        self.cookie_search_config = self.file_manager.load_config("../data/configs/cookie_search_config.json")
        self.password_search_config = self.file_manager.load_config("../data/configs/password_search_config.json")

        self.server_config = self.file_manager.load_config("../data/configs/server_config.json")
        self.api_config = self.file_manager.load_config("../data/configs/api_config.json")

        self.api_id = self.api_config["api_id"]
        self.api_hash = self.api_config["api_hash"]
        self.chat_id = self.api_config["chat_id"]
        self.bot_token = self.api_config["bot_token"]

        self.root_folder_path = self.server_config["root_folder_path"]

        self.database_manager = DatabaseManager.DatabaseManager(logger=self.logger, 
                                                                file_manager=self.file_manager,
                                                                cookie_search_config=self.cookie_search_config,
                                                                password_search_config=self.password_search_config)
        self.telegram_poster = TelegramPoster.TelegramPoster(logger=self.logger,
                                                             chat_id=self.chat_id, 
                                                             bot_token=self.bot_token)
        self.data_analysis = DataAnalysis.DataAnalysis(logger=self.logger,
                                                       telegram_poster=self.telegram_poster,
                                                       file_manager=self.file_manager, 
                                                       database_manager=self.database_manager,
                                                       cookie_search_config=self.cookie_search_config,
                                                       password_search_config=self.password_search_config)
        self.local_search_manager = LocalSearchManager.LocalSearchManger(logger=self.logger,
                                                                         root_folder_path=self.root_folder_path,
                                                                         data_analysis=self.data_analysis)
        self.telegram_downloader = TelegramDownloader.TelegramDownloader(logger=self.logger,
                                                                         file_manager=self.file_manager, 
                                                                         data_analysis=self.data_analysis, 
                                                                         download_path='../data/log_files')

    def start_listening(self):
        with TelegramClient('../data/misc/session_0001', int(self.api_id), self.api_hash) as client:
            # Create an asyncio queue to handle incoming messages
            message_queue = asyncio.Queue()

            @client.on(events.NewMessage())
            async def handler(event):
                chat = await event.get_chat()

                if hasattr(chat, 'title'): 
                    chat_name = chat.title #group
                else: 
                    chat_name = f"{chat.first_name} {chat.last_name}" #person

                await message_queue.put((event, chat_name))

            # Start a message processing loop
            asyncio.ensure_future(self.process_messages(message_queue))

            # TODO check if client is logged in
            # self.logger.print_warning("User is not authorized. Check your API ID and API hash inside the config file.\n")
            # self.logger.print_info("You can find your API config here:")
            # self.logger.print_info(f"{Logger.CYAN}{os.path.abspath('../data/configs/api_config.json')}{Logger.ENDC}\n", True, False)
            # input("Press Enter to exit...")
            # return

            self.logger.print_info("Listening to incoming messages...\n\n\n")
            
            client.start()
            client.run_until_disconnected()

    async def process_messages(self, message_queue):
        while True:
            # Get the next message from the queue
            event, chat_name = await message_queue.get()
            
            # Process the message using your TelegramDownloader or other methods
            await self.telegram_downloader.handle_message(event, chat_name)

            # Mark the message as done in the queue
            message_queue.task_done()

    def run(self):
        self.animgif_to_ASCII_animation("../data/misc/intro.gif")
        self.print_logo()
        self.logger.print_info("Server Started!\n", True)
        
        config_flag = False
        if not self.api_id:
            self.logger.print_warning(" > You have not specified a Telegram API ID yet!")
            config_flag = True

        if not self.api_hash:
            self.logger.print_warning(" > You have not specified a Telegram API hash yet!")
            config_flag = True

        if not self.chat_id:
            self.logger.print_warning(" > You have not specified a Telegram chat ID yet!")
            config_flag = True

        if not self.bot_token:
            self.logger.print_warning(" > You have not specified a Telegram bot token yet!")
            config_flag = True

        if not self.root_folder_path:
            self.logger.print_warning(" > You have not specified a root folder to support local scans!")
            config_flag = True

        if config_flag:
            print("")
            self.logger.print_info("Specify the config value(s) mentioned above to continue.", True)
            self.logger.print_info("You can find your configs here:")
            self.logger.print_info(f"{Logger.CYAN}{os.path.abspath('../data/configs/')}{Logger.ENDC}\n", True, False)
            input("Press Enter to exit...")
            return

        if not self.cookie_search_config and not self.password_search_config:
            self.logger.print_warning("Nothing to search for, because all search configs are empty!")
            self.logger.print_info("Closing server.\n")
            input("Press Enter to exit...")
            return
        
        self.logger.print_info("Select a working mode to run Lupin:", True)
        self.logger.print_info(" > [1] Listen to incoming Telegram messages")
        self.logger.print_info(" > [2] Scan Local Folder\n")
        while True:
            mode_string = input("           Enter a mode number: ")
            try:
                mode_number = int(mode_string)
                if mode_number == 1 or mode_number == 2:
                    break
                else:
                    self.logger.print_warning("Invalid mode number. Please enter 1 or 2.\n", True)
            except ValueError:
                self.logger.print_warning("Invalid input. Please enter a valid number.\n", True)

        print("")
        if mode_number == 1:
            self.logger.print_info("Selected mode: Listen to incoming Telegram messages", True)
            self.start_listening()
        elif mode_number == 2:
            self.logger.print_info("Selected mode: Scan Local Folder", True)
            self.local_search_manager.scan_root_folder()


    def print_logo(self):
        print("")
        print(f"     ▓██▓      ▓███     ▓██▓  ▓██████▓▓    ▓██▓  ▓██▓     ▓██▓")
        print(f"     ▓██▓      ▓██▓     ▓██▓  █████████▓   ███▓  ████     ███▓")
        print(f"     ███▓      ▓██▓     ███▓ ▓███▓▓▓▓███▓ ▓███  ▓████▓    ██▓ ")
        print(f"    ▓███       ███▓     ███  ▓███    ▓██▓ ▓██▓  ▓█████   ▓██▓ ")
        print(f"    ▓██▓       ███▓     ███  ▓██▓    ▓██▓ ▓██▓  ▓█████▓  ▓██▓ ")
        print(f"    ▓██▓      ▓███     ▓██▓  ▓██▓    ███▓ ███▓  ███▓███▓ ▓██▓ ")
        print(f"    ▓██▓      ▓███     ▓██▓  ███▓   ▓██▓  ███▓  ███▓▓██▓ ███  ")
        print(f"    ███▓      ▓██▓     ███▓ ▓██████████▓  ███   ███ ▓███▓███  ")
        print(f"   ▓███       ▓██▓    ▓███  ▓████████▓   ▓███  ▓██▓  ▓█████▓  ")
        print(f"   ▓██▓       ▓██▓    ▓██▓  ▓██▓▓▓▓▓     ▓██▓  ▓██▓  ▓█████▓  ")
        print(f"   ▓███       ▓███▓▓▓████▓  ▓██▓         ▓██▓  ▓██▓   ▓████▓  ")
        print(f"   ████▓▓▓▓▓   █████████▓   ███▓         ███▓  ███     ████   ")
        print(f"   █████████    ▓█████▓    ▓███▓        ▓███  ▓███     ▓███   ")
        print(f"   ▓▓▓▓▓▓▓▓▓     ▓▓▓▓▓     ▓▓▓▓         ▓▓▓▓  ▓▓▓▓     ▓▓▓▓  {Logger.BOLD}{Logger.CYAN}v{self.version}{Logger.ENDC}\n")

    # This is some Stack overflow Code
    def animgif_to_ASCII_animation(self, animated_gif_path):
        # map greyscale to characters
        chars = ('█', ' ', ' ', '▓', ' ', ' ', '▓', ' ', ' ', ' ', ' ')
        clear_console = 'clear' if os.name == 'posix' else 'CLS'

        # load image
        anim = pyglet.image.load_animation(animated_gif_path)

        # Step through forever, frame by frame
        for frame in anim.frames:

            # Gets a list of luminance ('L') values of the current frame
            data = frame.image.get_data('L', frame.image.width)

            # Built up the string, by translating luminance values to characters
            outstr = ''
            for (i, pixel) in enumerate(data):
                outstr += chars[int((pixel * (len(chars) - 1)) / 255)] + ('\n' if (i + 1) % frame.image.width == 0 else '')

            # Clear the console
            os.system(clear_console)

            # Write the current frame on stdout and sleep
            sys.stdout.write(outstr)
            sys.stdout.flush()
            time.sleep(0.06)
        
        os.system(clear_console)

server = Server()
server.run()
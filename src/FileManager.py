import os
import patoolib
import zipfile
import datetime
import subprocess
import json

class FileManager:
    def __init__(self, logger):
        self.logger = logger

    def remove_tree(self, directory):
        # sub processes are being used because windows is a little bitch and shutil/os python commands won't work (path length?)
        try:
            if os.name == 'nt':  # Windows
                subprocess.run(f'rmdir /s /q "{directory}"', check=True, shell=True)
            else:  # Linux or other Unix-like systems
                subprocess.run(["rm", "-rf", directory], check=True)
        except Exception as e:
            self.logger.print_error(f"Using: rmdir /s /q {os.path.abspath(directory)}")
            self.logger.print_error(f"ERROR: {e}")

    def convert_rar_to_zip(self, rar_file_path, rar_file_name, password=None):
        self.logger.print_info("Extracting .RAR ...")
        try:
            file_name, _ = os.path.splitext(rar_file_name)
            # Define the directory where the RAR contents will be extracted
            extraction_dir = f"../data/temp/{file_name}"

            # Use patoolib to extract the RAR file with the provided password
            patoolib.extract_archive(rar_file_path, verbosity=-1, outdir=extraction_dir, password=password)
            self.logger.print_success(".RAR finished extracting!")

            self.logger.print_info("Creating .ZIP ...")
            # Create a new ZIP file for writing
            zip_file_path = f"../data/log_files/{file_name}.zip"
            with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(extraction_dir):
                    for file in files:
                        try:
                            file_path = os.path.join(root, file)
                            
                            if "filegrabber" in file_path.lower() or "file grabber" in file_path.lower():
                                continue

                            # Add each extracted file to the ZIP archive
                            zipf.write(file_path, os.path.relpath(file_path, extraction_dir))
                        except:
                            self.logger.print_warning(f"Exluding bad file from .ZIP: {file}")
                            pass
            
            self.logger.print_success(".ZIP created!")

            # Clean up the temporary extraction directory
            self.logger.print_info("Cleaning directory...")
            self.remove_tree(extraction_dir)
            os.remove(rar_file_path)

            self.logger.print_success("Finished conversion!")

            return zip_file_path, f"{file_name}.zip" # Conversion successful
        except Exception as e:
            self.logger.print_error(f"Error: {e}")

            # cleaning temp folder and removing .rar and .zip
            if os.path.exists(extraction_dir):
                self.logger.print_info("Cleaning temp directory...")
                self.remove_tree(extraction_dir)

            if os.path.exists(rar_file_path):
                self.logger.print_info("Removing .RAR ...")
                os.remove(rar_file_path)

            if zip_file_path and os.path.exists(zip_file_path):
                self.logger.print_info("Removing .ZIP ...")
                os.remove(zip_file_path)

            self.logger.print_warning("Done handling exeption!")

            return "", ""  # Incorrect password or other error

    def compress_into_zip(self):
        try:
            # Use patoolib to compress the folder into a ZIP file
            output_path = f"../posted_logs/{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.zip"
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk("../data/output"):
                    for file in files:
                        try:
                            file_path = os.path.join(root, file)

                            # Add each extracted file to the ZIP archive
                            zipf.write(file_path, os.path.relpath(file_path, "../data/output"))
                        except:
                            self.logger.print_warning(f"Bad filename: {file}")
                            pass

            return output_path
        except Exception as e:
            print(f"Error occured while creating .ZIP {str(e)}")
            return ""
    
    def clear_output_subfolders(self):
        subfolders = [f"../data/output/Passwords/{subfolder}" for subfolder in os.listdir("../data/output/Passwords")] + [f"../data/output/Cookies/{subfolder}" for subfolder in os.listdir("../data/output/Cookies")]

        for folder in subfolders:
            for file in os.listdir(folder):
                file_path = os.path.join(folder, file)
                os.remove(file_path)
            os.rmdir(folder)
    
    def load_config(self, path):
        json_data = {}
        try:
            with open(path, 'r') as config_file:
                json_data = json.load(config_file)
        except:
            pass
        
        return json_data
    
    def save_cookies(self, file_name, cookies, type_name):
        if not cookies:
            return

        dir_name = f"../data/output/Cookies/{type_name}"
        os.makedirs(dir_name, exist_ok=True)
        output_file_path = os.path.join(dir_name, file_name)

        with open(output_file_path, 'wb') as f:
            for cookie in cookies:
                f.write(cookie)
    
    def save_passwords(self, file_name, usernames_passwords, type_name):
        if not usernames_passwords:
            return

        dir_name = f"../data/output/Passwords/{type_name}"
        os.makedirs(dir_name, exist_ok=True)
        output_file_path = os.path.join(dir_name, file_name)

        with open(output_file_path, 'wb') as f:
            for username, password in usernames_passwords:
                username_str = username.decode('utf-8')
                password_str = password.decode('utf-8')

                f.write(f'{username_str}:{password_str}\n'.encode('utf-8'))

    def save_auth_key(self, license_key):
        with open("../data/configs/server_config.json", 'r+') as file:
            data = json.load(file)
            data['license'] = license_key
            file.seek(0)
            file.truncate()
            json.dump(data, file, indent=4)
            file.close()
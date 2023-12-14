import os

class LocalSearchManger:
    def __init__(self, logger, root_folder_path, data_analysis):
        self.logger = logger
        self.root_folder_path = root_folder_path
        self.data_analysis = data_analysis

    def scan_root_folder(self):
        try:
            total_logs = len(os.listdir(self.root_folder_path))
        except:
            self.logger.print_error(f"The filepath '{self.root_folder_path}' could not be opened!", True)
            return

        self.logger.print_info(f"{total_logs} files were found!", True)
        if total_logs == 0:
            return
        self.logger.print_info("Press Enter to start scanning...\n") 
        input()

        for i, log_file in enumerate(os.listdir(self.root_folder_path)):
        
            file_path = os.path.join(self.root_folder_path, log_file)

            self.logger.print_info(f"[{i + 1}/{total_logs}]", True)
            
            if log_file.endswith('.zip'):
                self.data_analysis.start_scanning(file_path, log_file, False)
            else:
                self.logger.print_warning(f"Skipping '{log_file}' because it's not supported!\n")

    
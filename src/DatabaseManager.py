import sqlite3

class DatabaseManager:
    def __init__(self, logger, file_manager, cookie_search_config, password_search_config):
        self.logger = logger
        self.file_manager = file_manager

        self.cookie_search_config = cookie_search_config
        self.password_search_config = password_search_config

        # COOKIE 
        self.cookie_connection = sqlite3.connect("../data/databases/cookies.db")
        self.cookie_cursor = self.cookie_connection.cursor()
        for table_name, _ in self.cookie_search_config.items(): # remove Numbers and just leave [a-z]
            create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS {table_name.replace(" ", "_").replace(".", "_")} ( 
                    id INTEGER PRIMARY KEY,
                    cookie BLOB UNIQUE NOT NULL
                )
            """
            self.cookie_cursor.execute(create_table_sql)
        self.cookie_connection.commit()
        self.cookie_connection.close()

        # CREDENTIAL 
        self.credential_connection = sqlite3.connect("../data/databases/passwords.db")
        self.credential_cursor = self.credential_connection.cursor()
        for table_name, _ in self.password_search_config.items():
            create_table_sql = f'''
                CREATE TABLE IF NOT EXISTS {table_name.replace(" ", "_").replace(".", "_")} (
                    id INTEGER PRIMARY KEY,
                    username BLOB NOT NULL,
                    password BLOB NOT NULL
                )
            '''
            self.credential_cursor.execute(create_table_sql) 
        self.credential_connection.commit()
        self.credential_connection.close()

    def open(self):
        self.cookie_connection = sqlite3.connect("../data/databases/cookies.db")
        self.cookie_cursor = self.cookie_connection.cursor()

        self.credential_connection = sqlite3.connect("../data/databases/passwords.db")
        self.credential_cursor = self.credential_connection.cursor()

    def close(self):
        self.cookie_connection.commit()
        self.cookie_connection.close()

        self.credential_connection.commit()
        self.credential_connection.close()
    
    def add_cookie_to_database(self, table_name: str, data: bytes):
        self.cookie_cursor.execute(f"INSERT INTO {table_name.replace(' ', '_')} (cookie) VALUES (?)", (data,))
        self.cookie_connection.commit()

    def add_credential_to_database(self, table_name: str, username: bytes, password: bytes):
        self.credential_cursor.execute(f"INSERT INTO {table_name.replace(' ', '_')} (username, password) VALUES (?, ?)", (username, password))
        self.credential_connection.commit()
    
    def cookie_exists(self, table_name: str, data: bytes) -> bool:
        # Check if the cookie exists in the table
        self.cookie_cursor.execute(f"SELECT EXISTS (SELECT 1 FROM {table_name.replace(' ', '_')} WHERE cookie = ?)", (data,))
        return self.cookie_cursor.fetchone()[0] == 1

    def credential_exists(self, table_name: str, username: bytes, password: bytes) -> bool:
        # Check if the credential exists in the table
        self.credential_cursor.execute(f"SELECT EXISTS (SELECT 1 FROM {table_name.replace(' ', '_')} WHERE username = ? AND password = ?)", (username, password))
        return self.credential_cursor.fetchone()[0] == 1
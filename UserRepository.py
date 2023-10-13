import re
import bcrypt
from google.cloud.sql.connector import Connector
import os
import tempfile
import streamlit as st


class UserRepository:
    def __init__(self):
        self.connection = None

    def connect(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
            temp_file_path = temp_file.name

        # Use the temporary file path as the value for GOOGLE_APPLICATION_CREDENTIALS
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_file_path

        instance_connection_name = os.environ[
            "MYSQL_CONNECTION_STRING"
        ]
        db_user = os.environ["SQL_USERNAME"]
        db_pass = os.environ["SQL_PASSWORD"]
        db_name = os.environ["SQL_DATABASE"]

        self.connection = Connector().connect(
            instance_connection_name,
            "pymysql",
            user=db_user,
            password=db_pass,
            db=db_name,
        )
        self.create_users_table()

    def create_users_table(self):
        cursor = self.connection.cursor()
        create_table_query = """CREATE TABLE IF NOT EXISTS users (
                                    id INT AUTO_INCREMENT PRIMARY KEY,
                                    name VARCHAR(255) UNIQUE,
                                    username VARCHAR(255) UNIQUE,
                                    email VARCHAR(255) UNIQUE,
                                    password VARCHAR(255),
                                    is_enabled BOOLEAN DEFAULT TRUE
                                ); """
        cursor.execute(create_table_query)
        self.connection.commit()

    @staticmethod
    def is_valid_username(username):
        # Add your username validation logic here
        # For example, let's say the username should be at least 5 characters and only contain alphanumeric characters
        if len(username) < 5 or not username.isalnum():
            return False
        return True

    @staticmethod
    def is_valid_password(password):
        if len(password) < 8:
            return False
        if not re.search("[a-z]", password):
            return False
        if not re.search("[A-Z]", password):
            return False
        if not re.search("[0-9]", password):
            return False
        return True

    @staticmethod
    def is_valid_email(email):
        # Regular expression for validating an Email
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

        if re.search(email_regex, email):
            return True
        else:
            return False

    def register_user(self, name, username, email, password):
        cursor = self.connection.cursor()
        if not self.is_valid_username(username):
            return False, "Invalid username. It should be at least 5 characters and only contain alphanumeric " \
                          "characters. "

        if not self.is_valid_password(password):
            return False, "Invalid password. It should be at least 8 characters, contain at least one digit, " \
                          "one lowercase, one uppercase, and one special character. "

        if not self.is_valid_email(email):
            return False, "Invalid email. Please enter a valid email address."

        # Check if the username or email already exists
        cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
        existing_user = cursor.fetchone()
        if existing_user:
            return False, "Username or email already exists."

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        add_user_query = """INSERT INTO users (name, username, email, password)
                            VALUES (%s, %s, %s, %s);"""
        cursor.execute(add_user_query, (name, username, email, hashed_password))
        self.connection.commit()
        return True, f"User {username} with email {email} registered successfully."

    def enable_disable_user(self, username, enable=True):
        cursor = self.connection.cursor()
        update_query = """UPDATE users SET is_enabled = %s WHERE username = %s;"""
        cursor.execute(update_query, (enable, username))
        self.connection.commit()

    def authenticate_user(self, username, password):
        cursor = self.connection.cursor()
        find_user_query = """SELECT password, is_enabled FROM users WHERE username = %s;"""
        cursor.execute(find_user_query, (username,))
        result = cursor.fetchone()

        if result:
            stored_hashed_password, is_enabled = result
            if is_enabled and bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password.encode('utf-8')):
                return True
            else:
                return False
        else:
            return False

    def close(self):
        if self.connection:
            self.connection.close()

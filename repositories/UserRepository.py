import bcrypt
import os

import pymysql.cursors

from enums.UserType import UserType


class UserRepository:
    def __init__(self, connection):
        self.connection = connection
        #self.create_user_groups_table()
        #self.create_avatars_table()
        #self.create_users_table()
        self.create_root_user()
        # self.create_avatars()

    def create_avatars_table(self):
        with self.connection.cursor() as cursor:
            create_table_query = """
                CREATE TABLE IF NOT EXISTS `avatars` (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) UNIQUE,
                user_type ENUM('admin', 'teacher', 'student') NOT NULL,
                is_assigned BOOLEAN DEFAULT FALSE
            ); """

            cursor.execute(create_table_query)
            self.connection.commit()

    def create_users_table(self):
        with self.connection.cursor() as cursor:
            create_table_query = """
            CREATE TABLE IF NOT EXISTS `users` (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) UNIQUE,
                username VARCHAR(255) UNIQUE,
                email VARCHAR(255) UNIQUE,
                password VARCHAR(255),
                is_enabled BOOLEAN DEFAULT TRUE,
                user_type ENUM('admin', 'teacher', 'student') NOT NULL,
                group_id INT,
                org_id INT,
                avatar_id INT DEFAULT NULL,
                FOREIGN KEY (group_id) REFERENCES `user_groups`(id),
                FOREIGN KEY (org_id) REFERENCES `organizations`(id),
                FOREIGN KEY (avatar_id) REFERENCES `avatars`(id)
            );
            """
            cursor.execute(create_table_query)
            self.connection.commit()

    def create_user_groups_table(self):
        cursor = self.connection.cursor()
        create_table_query = """CREATE TABLE IF NOT EXISTS `user_groups` (
                                    id INT AUTO_INCREMENT PRIMARY KEY,
                                    name VARCHAR(255) UNIQUE,
                                    description TEXT,
                                    org_id INT,  
                                    FOREIGN KEY (org_id) REFERENCES `organizations`(id)  
                                ); """
        cursor.execute(create_table_query)
        self.connection.commit()

    def create_root_user(self):
        # Validate environment variables
        if 'ROOT_USER' not in os.environ or 'ROOT_PASSWORD' not in os.environ:
            print("Environment variables for root user are not set.")
            return

        root_user = os.environ['ROOT_USER']
        root_password = os.environ['ROOT_PASSWORD']

        # Check if the root user already exists
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM users WHERE username = %s", (root_user,))
        existing_user = cursor.fetchone()

        if existing_user:
            return

        # Hash the root user's password
        hashed_password = bcrypt.hashpw(root_password.encode('utf-8'), bcrypt.gensalt())

        # SQL query to insert the root user
        insert_root_user_query = """INSERT INTO users (name, username, email, password, 
                                    is_enabled, user_type, group_id, org_id) 
                                    VALUES ('root', %s, 'kaaimd@gmail.com', %s, TRUE, 'admin', NULL, NULL);"""

        # Execute the query
        cursor.execute(insert_root_user_query, (root_user, hashed_password.decode('utf-8'),))
        self.connection.commit()
        print(f"Root user {root_user} has been created.")

    def get_user(self, user_id):
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Query to select the user with the given user_id
            cursor.execute("""
                SELECT * FROM users
                WHERE id = %s;
            """, (user_id,))
            # Fetch one result
            result = cursor.fetchone()
            return result

    def add_user_to_group(self, username, group_name):
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM user_groups WHERE name = %s", (group_name,))
        group_id = cursor.fetchone()[0]

        cursor.execute("UPDATE users SET group_id = %s WHERE username = %s", (group_id, username))
        self.connection.commit()

    def assign_user_to_group(self, user_id, group_id):
        cursor = self.connection.cursor()
        assign_query = """UPDATE users SET group_id = %s WHERE id = %s;"""
        cursor.execute(assign_query, (group_id, user_id))
        self.connection.commit()

    def get_group_by_user_id(self, user_id):
        cursor = self.connection.cursor()
        query = """SELECT g.id, g.name 
                   FROM user_groups g
                   INNER JOIN users u ON g.id = u.group_id
                   WHERE u.id = %s;"""
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        self.connection.commit()

        if result:
            return {'group_id': result[0], 'group_name': result[1]}
        else:
            return {'group_id': None, 'group_name': None}

    def create_user_group(self, group_name, org_id):
        cursor = self.connection.cursor()

        # Check if the group already exists
        check_query = """SELECT COUNT(*) FROM user_groups WHERE name = %s;"""
        cursor.execute(check_query, (group_name,))
        count = cursor.fetchone()[0]

        if count > 0:
            return False, f"Team {group_name} already exists."

        # If the group doesn't exist, proceed to create it
        create_query = """INSERT INTO user_groups (name, org_id) VALUES (%s, %s);"""
        try:
            cursor.execute(create_query, (group_name, org_id))
            self.connection.commit()
            return True, f"Team {group_name} successfully created."
        except Exception as e:
            self.connection.rollback()  # Rollback the transaction in case of an error
            return False, f"Failed to create group '{group_name}'. Error: {str(e)}"

    def register_user(self, name, username, email, password,
                      org_id, user_type=UserType.STUDENT.value, avatar_id=None):
        try:
            with self.connection.cursor() as cursor:
                # Check if the username or email already exists
                cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
                existing_user = cursor.fetchone()
                if existing_user:
                    return False, "Username or email already exists.", None

                # Hash the password
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

                # Begin a new transaction
                self.connection.begin()

                # Insert new user record with avatar_id
                add_user_query = """
                                INSERT INTO users (name, username, email, password, org_id, user_type, avatar_id)
                                VALUES (%s, %s, %s, %s, %s, %s, %s);
                            """
                cursor.execute(add_user_query, (name, username, email, hashed_password, org_id, user_type, avatar_id))

                # Get the ID of the newly registered user
                user_id = cursor.lastrowid

                # If an avatar_id was provided, update the avatars table
                if avatar_id is not None:
                    cursor.execute("""
                        UPDATE avatars
                        SET is_assigned = TRUE
                        WHERE id = %s;
                    """, (avatar_id,))

                # Commit the transaction
                self.connection.commit()

                return True, f"User {username} with email {email} registered successfully as {user_type}.", user_id
        except Exception as e:
            # If an error occurs, roll back the transaction
            self.connection.rollback()
            return False, f"Failed to register user due to error: {e}", None

    def get_all_avatars(self):
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT * FROM avatars;
            """)
            # Fetch all results
            results = cursor.fetchall()
            return results

    def get_avatar_by_name(self, name):
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Query to select the avatar with the given name
            cursor.execute("""
                SELECT * FROM avatars
                WHERE name = %s;
            """, name)
            # Fetch one result
            result = cursor.fetchone()
            return result

    def get_available_avatars(self, user_type=UserType.STUDENT):
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Select avatars that are not yet assigned
            cursor.execute("""
                SELECT * FROM avatars
                WHERE user_type = %s and is_assigned IS FALSE;
            """, user_type.value)
            # Fetch all results
            results = cursor.fetchall()
            return results

    def get_avatar(self, user_id):
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Join users table with avatars table to get the avatar object
            cursor.execute("""
                SELECT av.*
                FROM users AS u
                JOIN avatars AS av ON u.avatar_id = av.id
                WHERE u.id = %s;
            """, (user_id,))
            result = cursor.fetchone()

            # Return the avatar object as a dictionary if available, else return None
            return result if result else None

    def enable_disable_user(self, username, enable=True):
        cursor = self.connection.cursor()
        update_query = """UPDATE users SET is_enabled = %s WHERE username = %s;"""
        cursor.execute(update_query, (enable, username))
        self.connection.commit()

    def authenticate_user(self, username, password):
        cursor = self.connection.cursor()
        find_user_query = """SELECT id, org_id, password, is_enabled, group_id
                             FROM users WHERE username = %s;"""
        cursor.execute(find_user_query, (username,))
        result = cursor.fetchone()

        if result:
            user_id, org_id, stored_hashed_password, is_enabled, group_id = result
            if is_enabled and bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password.encode('utf-8')):
                return True, user_id, org_id, group_id
            else:
                return False, -1, -1, -1
        else:
            return False, -1, -1, -1

    def change_password(self, username, email, new_password):
        cursor = self.connection.cursor()

        # Verify that the username and email match
        find_user_query = """SELECT id FROM users WHERE username = %s AND email = %s;"""
        cursor.execute(find_user_query, (username, email))
        result = cursor.fetchone()

        # If the user exists
        if result:
            user_id = result[0]

            # Hash the new password
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

            # Update the user's password in the database
            update_password_query = """UPDATE users SET password = %s WHERE id = %s;"""
            cursor.execute(update_password_query, (hashed_password.decode('utf-8'), user_id))
            self.connection.commit()

            return True, "Password updated successfully."

        else:
            return False, "Username or email does not match our records."

    def get_all_users(self, org_id):
        with self.connection.cursor() as cursor:
            # SQL query to select users from a specific organization
            get_users_query = """SELECT id, username FROM users WHERE org_id = %s;"""
            cursor.execute(get_users_query, (org_id,))  # Pass org_id as a parameter to the query
            result = cursor.fetchall()
            users = [{'user_id': row[0], 'username': row[1]} for row in result]
        return users

    def get_group(self, group_id):
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            get_group_query = """
                    SELECT id, name
                    FROM user_groups 
                    WHERE id = %s;
                    """
            cursor.execute(get_group_query, (group_id,))
            return cursor.fetchone()

    def get_all_groups(self, org_id):
        cursor = self.connection.cursor()
        get_groups_query = """
                SELECT ug.id, ug.name, COUNT(u.id) as member_count
                FROM user_groups ug
                LEFT JOIN users u ON ug.id = u.group_id
                WHERE ug.org_id = %s
                GROUP BY ug.id, ug.name;
                """
        cursor.execute(get_groups_query, (org_id,))
        result = cursor.fetchall()
        groups = [
            {'group_id': row[0], 'group_name': row[1], 'member_count': row[2]}
            for row in result
        ]
        return groups

    def get_users_by_org_id_group_and_type(self, org_id, group_id, user_type):
        cursor = self.connection.cursor()
        get_users_query = """SELECT u.id, u.name, u.username, u.email, g.name AS group_name 
                             FROM users u
                             LEFT JOIN user_groups g ON u.group_id = g.id
                             WHERE u.org_id = %s AND u.group_id = %s AND u.user_type = %s;"""
        cursor.execute(get_users_query, (org_id, group_id, user_type))
        result = cursor.fetchall()
        users = [{'id': row[0], 'name': row[1], 'username': row[2],
                  'email': row[3], 'group_name': row[4]} for row in result]
        return users

    def get_users_by_group(self, group_id):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        get_users_query = """SELECT u.id as user_id, u.name, u.username, u.email, g.name AS group_name 
                             FROM users u
                             LEFT JOIN user_groups g ON u.group_id = g.id
                             WHERE u.group_id = %s;"""
        cursor.execute(get_users_query, group_id)
        return cursor.fetchall()

    def get_admin_users_by_org_id(self, org_id):
        cursor = self.connection.cursor()
        get_users_query = """SELECT id, username, email FROM users WHERE org_id = %s AND user_type = 'admin';"""
        cursor.execute(get_users_query, (org_id,))
        result = cursor.fetchall()
        users = [{'id': row[0], 'username': row[1], 'email': row[2]} for row in result]
        return users

    def get_users_by_org_id_and_type(self, org_id, user_type):
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            get_users_query = """
            SELECT u.id, u.name, u.username, u.email, g.name AS group_name, a.name AS avatar
            FROM users u
            LEFT JOIN user_groups g ON u.group_id = g.id
            LEFT JOIN avatars a ON u.avatar_id = a.id
            WHERE u.org_id = %s AND u.user_type = %s;
            """
            cursor.execute(get_users_query, (org_id, user_type))
            return cursor.fetchall()

    def assign_user_to_org(self, user_id, org_id):
        cursor = self.connection.cursor()
        try:
            # Prepare the SQL query to update the org_id for the given user_id
            assign_query = """UPDATE users SET org_id = %s WHERE id = %s;"""

            # Execute the query
            cursor.execute(assign_query, (org_id, user_id))

            # Commit the changes to the database
            self.connection.commit()

            return True, f"User with ID {user_id} has been successfully assigned to organization with ID {org_id}."
        except Exception as e:
            # Rollback the transaction in case of an error
            self.connection.rollback()

            return False, f"Failed to assign user to organization. Error: {str(e)}"

    def create_avatars(self):
        # Query to check if the avatar already exists
        check_avatar_query = """
                SELECT COUNT(*) FROM avatars WHERE name = %s;
                """
        # Query to insert a new avatar if it does not exist
        insert_avatar_query = """
                INSERT INTO avatars (name, user_type, is_assigned)
                VALUES (%s, %s, %s);
                """

        with self.connection.cursor() as cursor:
            for i in range(1, 38):
                avatar_name = f"avatar {i}"
                # Check if avatar already exists
                cursor.execute(check_avatar_query, (avatar_name,))
                if cursor.fetchone()[0] == 0:
                    # Avatar does not exist, proceed to insert
                    cursor.execute(insert_avatar_query, (avatar_name, UserType.STUDENT.value, False))
                    self.connection.commit()

            for i in range(1, 2):
                avatar_name = f"teacher avatar {i}"
                # Check if avatar already exists
                cursor.execute(check_avatar_query, (avatar_name,))
                if cursor.fetchone()[0] == 0:
                    # Avatar does not exist, proceed to insert
                    cursor.execute(insert_avatar_query, (avatar_name, UserType.TEACHER.value, False))
                    self.connection.commit()



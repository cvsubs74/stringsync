import json
import pytz
import pymysql


class UserActivityRepository:
    def __init__(self, connection):
        self.connection = connection
        self.create_activities_table()

    def create_activities_table(self):
        cursor = self.connection.cursor()
        create_table_query = """
            CREATE TABLE IF NOT EXISTS `user_activities` (
                activity_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                activity_type ENUM('Log In', 'Log Out', 'Play Track', 'Upload Recording'),
                additional_params JSON,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES `users`(id)
            );
        """

        cursor.execute(create_table_query)
        self.connection.commit()

    def log_activity(self, user_id, activity_type, additional_params=None):
        if additional_params is None:
            additional_params = {}
        cursor = self.connection.cursor()
        insert_activity_query = """
            INSERT INTO user_activities (user_id, activity_type, additional_params)
            VALUES (%s, %s, %s);
        """
        # Convert the additional_params dictionary to a JSON string
        additional_params_json = json.dumps(additional_params) if additional_params else "{}"
        cursor.execute(insert_activity_query, (user_id, activity_type.value, additional_params_json))
        self.connection.commit()

    def get_user_activities(self, user_id, timezone='America/Los_Angeles'):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        query = """
            SELECT activity_id,
                   user_id,
                   activity_type,
                   additional_params,
                   timestamp
            FROM user_activities
            WHERE user_id = %s
            ORDER BY timestamp DESC;
        """
        cursor.execute(query, (user_id,))
        result = cursor.fetchall()
        for activity in result:
            # Deserialize the additional_params JSON string to a dictionary
            activity['additional_params'] = json.loads(activity['additional_params']) if activity[
                'additional_params'] else {}
            utc_timestamp = pytz.utc.localize(activity['timestamp'])
            local_tz = pytz.timezone(timezone)
            local_timestamp = utc_timestamp.astimezone(local_tz)
            activity['timestamp'] = local_timestamp
        return result

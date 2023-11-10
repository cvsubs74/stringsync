import pymysql
import pymysql.cursors

from enums.Badges import UserBadges


class UserPracticeLogRepository:
    def __init__(self, connection):
        self.connection = connection
        self.create_practice_log_table()

    def create_practice_log_table(self):
        cursor = self.connection.cursor()
        create_table_query = """
            CREATE TABLE IF NOT EXISTS `user_practice_logs` (
                log_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                timestamp DATETIME,
                minutes INT,
                FOREIGN KEY (user_id) REFERENCES `users`(id)
            );
        """
        cursor.execute(create_table_query)
        self.connection.commit()

    def fetch_logs(self, user_id):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        query = """
            SELECT * FROM user_practice_logs WHERE user_id = %s;
        """
        cursor.execute(query, (user_id,))
        return cursor.fetchall()

    def log_practice(self, user_id, timestamp, minutes):
        cursor = self.connection.cursor()
        insert_log_query = """
            INSERT INTO user_practice_logs (user_id, timestamp, minutes)
            VALUES (%s, %s, %s);
        """
        cursor.execute(insert_log_query, (user_id, timestamp, minutes))
        self.connection.commit()

    def get_streaks(self, user_id):
        cursor = self.connection.cursor()
        streaks = {
            '2_day_streak': 0,
            '3_day_streak': 0,
            '5_day_streak': 0,
            '7_day_streak': 0,
            '10_day_streak': 0
        }
        query = """
            SELECT DATEDIFF(MAX(timestamp), MIN(timestamp)) + 1 AS streak_length 
            FROM user_practice_logs 
            WHERE user_id = %s 
            GROUP BY DATE_SUB(timestamp, INTERVAL DATEDIFF(MAX(timestamp), timestamp) DAY)
        """
        cursor.execute(query, (user_id,))
        result = cursor.fetchall()

        for row in result:
            streak_length = row['streak_length']
            if streak_length >= 10:
                streaks['10_day_streak'] += 1
            elif streak_length >= 7:
                streaks['7_day_streak'] += 1
            elif streak_length >= 5:
                streaks['5_day_streak'] += 1
            elif streak_length >= 3:
                streaks['3_day_streak'] += 1
            elif streak_length >= 2:
                streaks['2_day_streak'] += 1

        return streaks

    def get_streak(self, user_id, practice_date):
        cursor = self.connection.cursor()
        query = """
                SELECT DISTINCT DATE(timestamp) as practice_date
                FROM user_practice_logs
                WHERE user_id = %s
                ORDER BY DATE(timestamp) DESC 
            """
        cursor.execute(query, (user_id,))
        result = cursor.fetchall()

        previous_date = practice_date
        streak = 1
        for row in result:
            current_date = row[0]
            day_diff = (previous_date - current_date).days
            if day_diff in [0, 1]:
                if day_diff == 1:
                    streak += 1
                    previous_date = current_date
            else:
                break
        # Determine the streak badge
        if streak >= 10:
            return UserBadges.TEN_DAY_STREAK
        elif streak >= 7:
            return UserBadges.SEVEN_DAY_STREAK
        elif streak >= 5:
            return UserBadges.FIVE_DAY_STREAK
        elif streak >= 3:
            return UserBadges.THREE_DAY_STREAK
        elif streak >= 2:
            return UserBadges.TWO_DAY_STREAK
        else:
            return None

    def fetch_daily_practice_minutes(self, user_id):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        query = """
            SELECT DATE(timestamp) as date, SUM(minutes) as total_minutes
            FROM user_practice_logs
            WHERE user_id = %s
            GROUP BY DATE(timestamp)
            ORDER BY DATE(timestamp)
        """
        cursor.execute(query, (user_id,))
        practice_data = cursor.fetchall()
        return practice_data







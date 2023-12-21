import datetime
import pymysql.cursors
from enums.Badges import UserBadges, TrackBadges
from enums.TimeFrame import TimeFrame


class UserAchievementRepository:
    def __init__(self, connection):
        self.connection = connection
        #self.create_achievements_table()

    def create_achievements_table(self):
        cursor = self.connection.cursor()
        create_table_query = """
            CREATE TABLE IF NOT EXISTS `user_achievements` (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                recording_id INT NULL,
                badge VARCHAR(255),
                value INT DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                award_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        cursor.execute(create_table_query)
        self.connection.commit()

    def award_user_badge_by_time_frame(self,
                                       user_id,
                                       badge: UserBadges,
                                       time_frame: TimeFrame,
                                       value=0):
        cursor = self.connection.cursor()

        start_date, end_date = time_frame.get_date_range()

        # Check if a badge record already exists for the given time frame
        cursor.execute(
            "SELECT COUNT(*) FROM user_achievements "
            "WHERE user_id = %s AND badge = %s AND DATE(timestamp) BETWEEN %s AND %s",
            (user_id, badge.value, start_date, end_date)
        )

        existing_badges_count = cursor.fetchone()[0]

        if existing_badges_count == 0:
            # If no existing badge, insert a new record
            cursor.execute(
                "INSERT INTO user_achievements (user_id, badge, timestamp, value) VALUES (%s, %s, %s, %s)",
                (user_id, badge.value, end_date, value)
            )
        else:
            # If badge exists, update the record
            cursor.execute(
                "UPDATE user_achievements SET value = %s "
                "WHERE user_id = %s AND badge = %s AND DATE(timestamp) BETWEEN %s AND %s",
                (value, user_id, badge.value, start_date, end_date)
            )

        self.connection.commit()
        return True, f"Awarded/Updated {badge.name} for user with ID {user_id} for {time_frame.name}"

    def award_user_badge(self, user_id, badge: UserBadges, timestamp=datetime.datetime.now()):
        cursor = self.connection.cursor()
        # Check for existing 'FIRST_NOTE' badge
        if badge == UserBadges.FIRST_NOTE:
            cursor.execute(
                "SELECT COUNT(*) FROM user_achievements "
                "WHERE user_id = %s AND badge = %s",
                (user_id, badge.value)
            )
        else:
            # Check for other badges awarded today
            cursor.execute(
                "SELECT COUNT(*) FROM user_achievements "
                "WHERE user_id = %s AND badge = %s AND DATE(timestamp) = DATE(%s)",
                (user_id, badge.value, timestamp)
            )

        existing_badges = cursor.fetchone()

        # If no existing 'FIRST_NOTE' badge or other badges not awarded today
        if existing_badges[0] == 0:
            # Award the new badge
            cursor.execute(
                "INSERT INTO user_achievements (user_id, badge, timestamp) VALUES (%s, %s, %s)",
                (user_id, badge.value, timestamp)
            )
            self.connection.commit()
            return True, f"Awarded {badge.name} to user with ID {user_id}"
        else:
            return False, f"User with ID {user_id} already has the {badge.name} badge"

    def award_track_badge(self, user_id, recording_id, badge: TrackBadges,
                          timestamp=datetime.datetime.now()):
        cursor = self.connection.cursor()
        # Enforce badge uniqueness at the track level
        cursor.execute(
            "SELECT COUNT(*) FROM user_achievements "
            "WHERE user_id = %s AND badge = %s AND recording_id = %s",
            (user_id, badge.value, recording_id)
        )
        existing_badges = cursor.fetchone()

        if existing_badges[0] == 0:
            # Award the new badge
            cursor.execute(
                "INSERT INTO user_achievements (user_id, badge, recording_id, timestamp) "
                "VALUES (%s, %s, %s, %s)",
                (user_id, badge.value, recording_id, timestamp)
            )
            self.connection.commit()
            return True, f"Awarded {badge.value} to user with ID {user_id}"
        else:
            return False, f"User with ID {user_id} already has the {badge.value} badge"

    def get_user_badges(self, user_id, time_frame: TimeFrame = TimeFrame.HISTORICAL):
        cursor = self.connection.cursor()

        if time_frame == TimeFrame.HISTORICAL:
            # For historical timeframe, fetch all records without timestamp constraint
            cursor.execute("SELECT badge FROM user_achievements WHERE user_id = %s", (user_id,))
        else:
            # For other timeframes, apply the timestamp constraints
            start_date, end_date = time_frame.get_date_range()
            cursor.execute("SELECT badge FROM user_achievements "
                           "WHERE user_id = %s AND timestamp BETWEEN %s AND %s",
                           (user_id, start_date, end_date))

        badges = cursor.fetchall()
        return [badge[0] for badge in badges]

    def get_user_badges_with_counts(self, user_id, time_frame: TimeFrame = TimeFrame.HISTORICAL):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)

        if time_frame == TimeFrame.HISTORICAL:
            # For historical timeframe, fetch all records without timestamp constraint and count them
            cursor.execute("""
                SELECT badge, COUNT(*) as count 
                FROM user_achievements 
                WHERE user_id = %s 
                GROUP BY badge
                """, (user_id,))
        else:
            # For other timeframes, apply the timestamp constraints and count
            start_date, end_date = time_frame.get_date_range()
            cursor.execute("""
                SELECT badge, COUNT(*) as count 
                FROM user_achievements 
                WHERE user_id = %s AND timestamp BETWEEN %s AND %s
                GROUP BY badge
                """, (user_id, start_date, end_date))

        return cursor.fetchall()

    def get_badge_by_recording(self, recording_id):
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT badge FROM user_achievements WHERE recording_id = %s",
            (recording_id,)
        )
        badge = cursor.fetchone()
        if badge:
            return badge[0]

        return None

    def get_user_achievements_by_timeframe(
            self, user_id, time_frame: TimeFrame = TimeFrame.PREVIOUS_WEEK):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        start_date, end_date = time_frame.get_date_range()
        cursor.execute("SELECT * FROM user_achievements "
                       "WHERE user_id = %s AND timestamp BETWEEN %s AND %s",
                       (user_id, start_date, end_date))
        results = cursor.fetchall()
        return list(results) if results else []

    def get_user_achievements_after_timestamp(self, user_id, timestamp):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)

        query = """
        SELECT ua.*, t.name AS track_name
        FROM user_achievements ua
        LEFT JOIN recordings r ON ua.recording_id = r.id
        LEFT JOIN tracks t ON r.track_id = t.id
        WHERE ua.user_id = %s AND ua.award_timestamp >= %s
        """
        cursor.execute(query, (user_id, timestamp))

        results = cursor.fetchall()
        return list(results) if results else []



from time import time
from datetime import datetime, timedelta
import pymysql
import pytz

from enums.TimeFrame import TimeFrame


class UserSessionRepository:
    def __init__(self, connection):
        self.connection = connection
        #self.create_sessions_table()

    def create_sessions_table(self):
        cursor = self.connection.cursor()
        create_table_query = """CREATE TABLE IF NOT EXISTS `user_sessions` (
                                    session_id VARCHAR(255) PRIMARY KEY,
                                    user_id INT,
                                    open_session_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                    close_session_time TIMESTAMP,
                                    last_activity_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                                    session_duration INT,
                                    is_open BOOLEAN DEFAULT TRUE,
                                    FOREIGN KEY (user_id) REFERENCES `users`(id)
                                ); """
        cursor.execute(create_table_query)
        self.connection.commit()

    def open_session(self, user_id):
        cursor = self.connection.cursor()

        # Check for any open sessions for the user
        check_open_session_query = """
            SELECT session_id, is_open
            FROM user_sessions
            WHERE user_id = %s
            ORDER BY open_session_time DESC
            LIMIT 1;
        """
        cursor.execute(check_open_session_query, (user_id,))
        result = cursor.fetchone()

        # If an open session is found, close it
        previous_session_id = None
        previous_session_open = False
        if result:
            previous_session_id = result[0]
            previous_session_open = result[1]
            if previous_session_open:
                self.close_session(previous_session_id)

        # Generate a new session ID and open a new session
        session_id = f'session-{user_id}-{int(time())}'  # Generating a simple session ID
        insert_session_query = """INSERT INTO user_sessions (session_id, user_id) VALUES (%s, %s);"""
        cursor.execute(insert_session_query, (session_id, user_id))
        self.connection.commit()

        cursor.close()  # close the cursor after use
        return session_id, previous_session_id, previous_session_open

    def close_session(self, session_id):
        cursor = self.connection.cursor()
        # Update the close_session_time, calculate session_duration, and set is_open to FALSE
        update_session_query = """
            UPDATE user_sessions
            SET close_session_time = last_activity_time,
                session_duration = TIMESTAMPDIFF(SECOND, open_session_time, last_activity_time),
                is_open = FALSE
            WHERE session_id = %s;
        """
        cursor.execute(update_session_query, (session_id,))
        self.connection.commit()

        # Fetch the session_duration
        fetch_duration_query = """
            SELECT session_duration
            FROM user_sessions
            WHERE session_id = %s;
        """
        cursor.execute(fetch_duration_query, (session_id,))
        result = cursor.fetchone()
        session_duration = 0
        if result:
            session_duration = result[0]

        cursor.close()  # close the cursor after use
        return session_duration

    def get_last_activity_time(self, session_id):
        cursor = self.connection.cursor()
        get_activity_time_query = """
            SELECT last_activity_time
            FROM user_sessions
            WHERE session_id = %s;
        """
        cursor.execute(get_activity_time_query, (session_id,))
        result = cursor.fetchone()
        # result will be None if there is no such session_id
        return result[0] if result else None

    def update_last_activity_time(self, session_id):
        cursor = self.connection.cursor()
        update_activity_time_query = """
            UPDATE user_sessions
            SET last_activity_time = CURRENT_TIMESTAMP,
                session_duration = TIMESTAMPDIFF(SECOND, open_session_time, CURRENT_TIMESTAMP)
            WHERE session_id = %s;
        """
        cursor.execute(update_activity_time_query, (session_id,))
        self.connection.commit()

    def is_session_open(self, session_id):
        cursor = self.connection.cursor()
        check_session_query = """SELECT is_open FROM user_sessions WHERE session_id = %s;"""
        cursor.execute(check_session_query, (session_id,))
        result = cursor.fetchone()
        return result[0] if result else None

    def get_user_sessions(self, user_id, timezone='America/Los_Angeles', limit=50):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        query = """
            SELECT session_id,
                   user_id,
                   open_session_time,
                   last_activity_time,
                   close_session_time,
                   session_duration,
                   is_open
            FROM user_sessions
            WHERE user_id = %s
            ORDER BY open_session_time DESC
            LIMIT %s;
        """
        cursor.execute(query, (user_id, limit))
        sessions = cursor.fetchall()
        for session in sessions:
            local_tz = pytz.timezone(timezone)
            # Open session time
            open_utc_timestamp = pytz.utc.localize(session['open_session_time'])
            local_open_timestamp = open_utc_timestamp.astimezone(local_tz)
            session['open_session_time'] = local_open_timestamp
            # Last activity time
            last_activity_utc_timestamp = pytz.utc.localize(session['last_activity_time'])
            local_last_activity_timestamp = last_activity_utc_timestamp.astimezone(local_tz)
            session['last_activity_time'] = local_last_activity_timestamp
            if not session['is_open']:
                # Close session time
                close_utc_timestamp = pytz.utc.localize(session['close_session_time'])
                local_close_timestamp = close_utc_timestamp.astimezone(local_tz)
                session['close_session_time'] = local_close_timestamp
        return sessions

    def get_time_series_data(self, user_id):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        query = """
            SELECT DATE(open_session_time) as date,
                   COALESCE(SUM(session_duration), 0) as total_duration,
                   COUNT(*) as total_sessions
            FROM user_sessions
            WHERE user_id = %s
            GROUP BY DATE(open_session_time)
            ORDER BY date ASC;
            """
        cursor.execute(query, (user_id,))
        result = cursor.fetchall()

        # If no results are found, return an empty list
        if not result:
            return []

        # Determine the earliest session date and the last day of the current month
        start_date = result[0]['date']
        current_year = datetime.now().year
        current_month = datetime.now().month

        # Handle December separately for the end date
        if current_month == 12:
            end_date = datetime(current_year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(current_year, current_month + 1, 1).date() - timedelta(days=1)

        # Initialize an empty list to hold the time series data
        all_days_data = []

        # Iterate through the days from the earliest session to the end of the current month
        current_date = start_date
        while current_date <= end_date:
            # Check if there is data for the current day in the query result
            day_data = next((item for item in result if item['date'] == current_date), None)

            if day_data:
                # Update the last known total_duration and total_sessions
                last_total_duration = day_data['total_duration']
                last_total_sessions = day_data['total_sessions']
            else:
                # Reset both total_duration and total_sessions to 0 for days without data
                last_total_duration = 0
                last_total_sessions = 0

            # Append the data for the current day to the list
            all_days_data.append({
                'date': current_date,
                'total_duration': last_total_duration,
                'total_sessions': last_total_sessions
            })

            # Move to the next day
            current_date += timedelta(days=1)
        return all_days_data

    def get_user_sessions_by_timeframe(
            self, user_id, time_frame: TimeFrame = TimeFrame.PREVIOUS_WEEK):
        cursor = self.connection.cursor()
        start_date, end_date = time_frame.get_date_range()
        cursor.execute("SELECT * FROM user_sessions "
                       "WHERE user_id = %s AND open_session_time BETWEEN %s AND %s",
                       (user_id, start_date, end_date))
        return cursor.fetchall()

    def get_user_last_activity_time(self, user_id):
        cursor = self.connection.cursor()
        query = """
            SELECT last_activity_time
            FROM user_sessions
            WHERE user_id = %s AND session_duration > 5
            ORDER BY last_activity_time DESC
            LIMIT 1
        """
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()

        # Close the cursor after use
        cursor.close()

        # Return the last activity time from the previous session if it exists, otherwise None
        return result[0] if result else None




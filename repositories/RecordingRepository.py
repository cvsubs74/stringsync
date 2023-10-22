import os
import tempfile
from google.cloud.sql.connector import Connector
import json


class RecordingRepository:
    def __init__(self):
        self.connection = self.connect()
        self.create_recordings_table()

    @staticmethod
    def connect():
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write(os.environ["GOOGLE_APP_CRED"])
            credentials_file_path = temp_file.name

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_file_path
        instance_connection_name = os.environ[
            "MYSQL_CONNECTION_STRING"
        ]
        db_user = os.environ["SQL_USERNAME"]
        db_pass = os.environ["SQL_PASSWORD"]
        db_name = os.environ["SQL_DATABASE"]

        return Connector().connect(
            instance_connection_name,
            "pymysql",
            user=db_user,
            password=db_pass,
            db=db_name,
        )

    def create_recordings_table(self):
        cursor = self.connection.cursor()
        create_table_query = """CREATE TABLE IF NOT EXISTS recordings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            track_id INT,
            blob_name VARCHAR(255),
            blob_url TEXT,
            timestamp DATETIME,
            duration INT,
            score INT,
            analysis TEXT,
            remarks TEXT,
            file_hash VARCHAR(32)  
        ); """
        cursor.execute(create_table_query)
        self.connection.commit()

    def add_recording(self, user_id, track_id, blob_name, blob_url, timestamp, duration, file_hash, analysis="", remarks=""):
        cursor = self.connection.cursor()
        add_recording_query = """INSERT INTO recordings (user_id, track_id, blob_name, blob_url, timestamp, duration, file_hash, analysis, remarks)
                                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);"""  # Include file_hash
        cursor.execute(add_recording_query, (user_id, track_id, blob_name, blob_url, timestamp, duration, file_hash, analysis, remarks))
        self.connection.commit()
        return cursor.lastrowid  # Return the id of the newly inserted row

    def is_duplicate_recording(self, user_id, track_id, file_hash):
        cursor = self.connection.cursor()
        query = """SELECT COUNT(*) FROM recordings
                   WHERE user_id = %s AND track_id = %s AND file_hash = %s;"""
        cursor.execute(query, (user_id, track_id, file_hash))
        count = cursor.fetchone()[0]
        return count > 0

    def get_recordings_by_user_id_and_track_id(self, user_id, track_id):
        cursor = self.connection.cursor()
        query = """SELECT id, blob_name, blob_url, timestamp, duration, track_id, score, analysis, remarks 
                   FROM recordings 
                   WHERE user_id = %s AND track_id = %s 
                   ORDER BY timestamp DESC;"""
        cursor.execute(query, (user_id, track_id))
        result = cursor.fetchall()

        # Convert the result to a list of dictionaries for better readability
        recordings = []
        for row in result:
            recording = {
                'id': row[0],
                'blob_name': row[1],
                'blob_url': row[2],
                'timestamp': row[3],
                'duration': row[4],
                'track_id': row[5],
                'score': row[6],
                'analysis': row[7],
                'remarks': row[8]
            }
            recordings.append(recording)

        return recordings

    def get_all_recordings_by_user(self, user_id):
        cursor = self.connection.cursor()
        get_recordings_query = """SELECT id, blob_name, blob_url, timestamp, duration, track_id, score, analysis, remarks FROM recordings
                                  WHERE user_id = %s
                                  ORDER BY timestamp DESC;"""
        cursor.execute(get_recordings_query, (user_id,))
        result = cursor.fetchall()

        # Convert the result to a list of dictionaries for better readability
        recordings = []
        for row in result:
            recording = {
                'id': row[0],  # New field
                'blob_name': row[1],
                'blob_url': row[2],
                'timestamp': row[3],
                'duration': row[4],
                'track_id': row[5],
                'score': row[6],
                'analysis': row[7],  # New field
                'remarks': row[8]  # New field
            }
            recordings.append(recording)

        return recordings

    def get_track_statistics_by_user(self, user_id):
        cursor = self.connection.cursor()

        # Query to get the number of recordings, max, min, and avg score for each track for a given user
        query = """SELECT track_id, COUNT(*), MAX(score), MIN(score), AVG(score) 
                   FROM recordings 
                   WHERE user_id = %s 
                   GROUP BY track_id;"""

        cursor.execute(query, (user_id,))
        result = cursor.fetchall()

        # Convert the result to a list of dictionaries for better readability
        track_statistics = []
        for row in result:
            stats = {
                'track_id': row[0],
                'num_recordings': row[1],
                'max_score': row[2],
                'min_score': row[3],
                'avg_score': row[4]
            }
            track_statistics.append(stats)

        return track_statistics

    def get_unique_tracks_by_user(self, user_id):
        cursor = self.connection.cursor()
        query = """SELECT DISTINCT track_id FROM recordings WHERE user_id = %s;"""
        cursor.execute(query, (user_id,))
        result = cursor.fetchall()
        return [row[0] for row in result]

    def update_score_and_analysis(self, recording_id, score, analysis):
        cursor = self.connection.cursor()
        update_query = """UPDATE recordings SET score = %s, analysis = %s WHERE id = %s;"""
        cursor.execute(update_query, (score, analysis, recording_id))
        self.connection.commit()

    def get_total_duration(self, user_id, track_id):
        cursor = self.connection.cursor()
        get_total_duration_query = """SELECT SUM(duration) FROM recordings
                                      WHERE user_id = %s AND track_id = %s;"""
        cursor.execute(get_total_duration_query, (user_id, track_id))
        return cursor.fetchone()[0]

    def update_remarks(self, recording_id, remarks):
        cursor = self.connection.cursor()
        update_query = """UPDATE recordings SET remarks = %s WHERE id = %s;"""
        cursor.execute(update_query, (remarks, recording_id))
        self.connection.commit()

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def __del__(self):
        self.close()

    def get_unremarked_recordings(self, group_id=None, user_id=None, track_id=None):
        cursor = self.connection.cursor()
        query = "SELECT id, blob_name, blob_url, timestamp, duration, track_id, score, analysis, remarks" \
                " FROM recordings WHERE remarks IS NULL OR remarks = ''"
        filters = []

        if group_id is not None:
            filters.append(f"group_id = {group_id}")

        if user_id is not None:
            filters.append(f"user_id = {user_id}")

        if track_id is not None:
            filters.append(f"track_id = {track_id}")

        if filters:
            query += " AND " + " AND ".join(filters)

        query += " ORDER BY timestamp DESC"

        cursor.execute(query)
        result = cursor.fetchall()
        self.connection.commit()
        recordings = []
        for row in result:
            recording = {
                'id': row[0],
                'blob_name': row[1],
                'blob_url': row[2],
                'timestamp': row[3],
                'duration': row[4],
                'track_id': row[5],
                'score': row[6],
                'analysis': row[7],
                'remarks': row[8]
            }
            recordings.append(recording)

        return recordings


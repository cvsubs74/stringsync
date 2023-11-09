import pymysql.cursors
from datetime import datetime, timedelta

import pytz


class RecordingRepository:
    def __init__(self, connection):
        self.connection = connection
        self.create_recordings_table()

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

    def add_recording(self, user_id, track_id, blob_name, blob_url,
                      timestamp, duration, file_hash, analysis="", remarks=""):
        cursor = self.connection.cursor()
        add_recording_query = """INSERT INTO recordings (user_id, track_id, blob_name, blob_url, timestamp, duration, file_hash, analysis, remarks)
                                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);"""
        cursor.execute(add_recording_query,
                       (user_id, track_id, blob_name, blob_url, timestamp, duration, file_hash, analysis, remarks))
        self.connection.commit()
        return cursor.lastrowid

    def is_duplicate_recording(self, user_id, track_id, file_hash):
        cursor = self.connection.cursor()
        query = """SELECT COUNT(*) FROM recordings
                   WHERE user_id = %s AND track_id = %s AND file_hash = %s;"""
        cursor.execute(query, (user_id, track_id, file_hash))
        count = cursor.fetchone()[0]
        return count > 0

    def recordings_exist_for_track(self, track_id):
        cursor = self.connection.cursor()
        query = """SELECT EXISTS (
                       SELECT 1 FROM recordings WHERE track_id = %s
                   ) AS recording_exists;"""
        cursor.execute(query, (track_id,))
        result = cursor.fetchone()
        return result[0] == 1

    def get_recordings_by_user_id_and_track_id(self, user_id, track_id):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        query = """SELECT id, blob_name, blob_url, timestamp, duration, track_id, score, analysis, remarks 
                   FROM recordings 
                   WHERE user_id = %s AND track_id = %s 
                   ORDER BY timestamp DESC;"""
        cursor.execute(query, (user_id, track_id))
        recordings = cursor.fetchall()
        return recordings

    def get_all_recordings_by_user(self, user_id):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        get_recordings_query = """SELECT id, blob_name, blob_url, timestamp, duration, 
                                  track_id, score, analysis, remarks 
                                  FROM recordings
                                  WHERE user_id = %s
                                  ORDER BY timestamp DESC;"""
        cursor.execute(get_recordings_query, (user_id,))
        recordings = cursor.fetchall()
        return recordings

    def get_track_statistics_by_user(self, user_id):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        query = """SELECT track_id, 
                          COALESCE(COUNT(*), 0) AS num_recordings, 
                          COALESCE(MAX(score), 0) AS max_score, 
                          COALESCE(MIN(score), 0) AS min_score, 
                          COALESCE(AVG(score), 0) as avg_score
                   FROM recordings 
                   WHERE user_id = %s 
                   GROUP BY track_id;"""

        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        return results

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

    def update_score(self, recording_id, score):
        cursor = self.connection.cursor()
        update_query = """UPDATE recordings SET score = %s WHERE id = %s;"""
        cursor.execute(update_query, (score, recording_id))
        self.connection.commit()

    def get_total_duration_by_track(self, user_id, track_id):
        cursor = self.connection.cursor()
        get_total_duration_query = """SELECT SUM(duration) FROM recordings
                                      WHERE user_id = %s AND track_id = %s;"""
        cursor.execute(get_total_duration_query, (user_id, track_id))
        return cursor.fetchone()[0]

    def get_total_duration(self, user_id, min_score=0):
        cursor = self.connection.cursor()
        get_total_duration_query = """SELECT SUM(duration) FROM recordings
                                      WHERE user_id = %s AND score >= %s;"""
        cursor.execute(get_total_duration_query, (user_id, min_score))
        result = cursor.fetchone()[0]
        return result if result is not None else 0

    def get_total_recordings(self, user_id, min_score=0):
        cursor = self.connection.cursor()
        get_total_recordings_query = """SELECT COUNT(*) FROM recordings
                                        WHERE user_id = %s AND score >= %s;"""
        cursor.execute(get_total_recordings_query, (user_id, min_score))
        return cursor.fetchone()[0]

    def update_remarks(self, recording_id, remarks):
        cursor = self.connection.cursor()
        update_query = """UPDATE recordings SET remarks = %s WHERE id = %s;"""
        cursor.execute(update_query, (remarks, recording_id))
        self.connection.commit()

    def get_recording_duration_by_date(self, user_id):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        query = """
            SELECT DATE(timestamp) as date, 
                   COALESCE(SUM(duration), 0) as total_duration,
                   COUNT(*) as total_tracks
            FROM recordings 
            WHERE user_id = %s 
            GROUP BY DATE(timestamp) 
            ORDER BY date ASC;
            """
        cursor.execute(query, (user_id,))
        result = cursor.fetchall()

        # If no results are found, return an empty list
        if not result:
            return []

        return result

    def get_average_scores_over_time(self, user_id):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        query = """
            SELECT DATE(timestamp) as date, AVG(score) as avg_score
            FROM recordings 
            WHERE user_id = %s AND score IS NOT NULL
            GROUP BY DATE(timestamp) 
            ORDER BY DATE(timestamp) ASC;
        """
        cursor.execute(query, (user_id,))
        result = cursor.fetchall()

        # Convert None values to a default value if necessary, e.g., 0
        for day in result:
            if day['avg_score'] is None:
                day['avg_score'] = 0

        return result


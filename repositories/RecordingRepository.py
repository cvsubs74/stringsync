import datetime

import pymysql.cursors
from components.TimeConverter import TimeConverter
from enums.TimeFrame import TimeFrame


class RecordingRepository:
    def __init__(self, connection):
        self.connection = connection
        #self.create_recordings_table()
        #self.create_user_track_table()

    def create_recordings_table(self):
        cursor = self.connection.cursor()
        create_table_query = """CREATE TABLE IF NOT EXISTS recordings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            track_id INT,
            assignment_id INT,  
            blob_name VARCHAR(255),
            blob_url TEXT,
            timestamp DATETIME,
            duration INT,
            score DECIMAL(4, 2),  -- Allowing up to 2 digits and 2 decimal places
            distance INT,
            analysis TEXT,
            remarks TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
            file_hash VARCHAR(32),
            is_training_data BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE SET NULL,
            FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE SET NULL
        );
        """
        cursor.execute(create_table_query)
        self.connection.commit()

    def create_user_track_table(self):
        cursor = self.connection.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS user_track (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            track_id INT,
            first_recommended_on DATETIME,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE
        );
        """
        cursor.execute(create_table_query)
        self.connection.commit()

    def get_recording(self, recording_id):
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = """
                    SELECT id, user_id, track_id, assignment_id, blob_name, blob_url,
                           timestamp, duration, score, distance, analysis, remarks, file_hash
                    FROM recordings
                    WHERE id = %s;
                    """
            cursor.execute(query, (recording_id,))
            recording = cursor.fetchone()
            return recording

    def add_recording(self, user_id, track_id, blob_name, blob_url, timestamp, duration, file_hash, analysis="",
                      remarks="", assignment_id=None):
        cursor = self.connection.cursor()
        add_recording_query = """INSERT INTO recordings (user_id, track_id, blob_name, blob_url, timestamp, duration, 
                                                         file_hash, analysis, remarks, assignment_id)
                                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""
        cursor.execute(add_recording_query,
                       (user_id, track_id, blob_name, blob_url, timestamp, duration, file_hash, analysis, remarks,
                        assignment_id))
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

    def get_recordings_by_ids(self, recording_ids):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        placeholders = ', '.join(['%s'] * len(recording_ids))
        query = f"""
            SELECT r.id, r.blob_name, r.blob_url, t.name AS track_name, t.track_path, r.timestamp, r.duration,
                   r.distance, t.offset, t.level,
                   r.track_id, r.score, r.analysis, r.remarks, r.user_id, u.name AS user_name, r.is_training_data,
                   ua.badge, ua.value AS badge_value
            FROM recordings r
            JOIN tracks t ON r.track_id = t.id
            JOIN users u ON r.user_id = u.id
            LEFT JOIN user_achievements ua ON r.id = ua.recording_id
            WHERE r.id IN ({placeholders});
        """
        cursor.execute(query, recording_ids)
        results = cursor.fetchall()
        return results

    def get_recordings_by_user_id_and_track_id(self, user_id, track_id, timezone='America/Los_Angeles'):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        query = """
                SELECT rec.id, rec.user_id, rec.blob_name, rec.blob_url, rec.timestamp, rec.duration, 
                       rec.track_id, rec.score, rec.distance, rec.remarks, rec.is_training_data, 
                       tr.name  AS track_name, tr.level, tr.offset, tr.track_path
                FROM recordings rec
                JOIN tracks tr ON rec.track_id = tr.id
                WHERE rec.user_id = %s AND rec.track_id = %s 
                ORDER BY rec.timestamp DESC;
                """
        cursor.execute(query, (user_id, track_id))
        recordings = cursor.fetchall()

        # Convert timestamp to local timezone
        for recording in recordings:
            local_timestamp = TimeConverter.convert_timestamp(
                recording['timestamp'], timezone)
            recording['timestamp'] = local_timestamp

        return recordings

    def get_recordings_by_user_id_and_track_id_and_assignment_id(
            self, user_id, track_id, assignment_id, timezone='America/Los_Angeles'):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        query = """SELECT id, user_id, blob_name, blob_url, timestamp, duration, track_id, score, remarks 
                   FROM recordings 
                   WHERE user_id = %s AND track_id = %s AND assignment_id = %s
                   ORDER BY timestamp DESC;"""
        cursor.execute(query, (user_id, track_id, assignment_id))
        recordings = cursor.fetchall()
        for recording in recordings:
            local_timestamp = TimeConverter.convert_timestamp(
                recording['timestamp'], timezone)
            recording['timestamp'] = local_timestamp

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
        query = """
        SELECT r.track_id, t.name as name, t.level as level,
               t.recommendation_threshold_score, 
               COALESCE(COUNT(*), 0) AS num_recordings, 
               COALESCE(MAX(r.score), 0) AS max_score, 
               COALESCE(MIN(r.score), 0) AS min_score,
               MIN(r.timestamp) AS earliest_recording_date,
               MAX(r.timestamp) AS latest_recording_date
        FROM recordings r
        LEFT JOIN tracks t ON r.track_id = t.id
        WHERE r.user_id = %s and r.score < 10.00
        GROUP BY r.track_id, t.name, t.recommendation_threshold_score
        ORDER BY t.level, t.ordering_rank;
        """
        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        return results

    def get_average_track_scores_by_user(self, user_id):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        query = """
        SELECT track_id, AVG(score) AS avg_score
        FROM (
            SELECT track_id, score,
                   ROW_NUMBER() OVER (PARTITION BY track_id ORDER BY score DESC) as score_rank
            FROM recordings
            WHERE user_id = %s AND score < 10.00
        ) AS ranked_scores
        WHERE score_rank <= 3
        GROUP BY track_id;
        """
        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        return results

    def get_all_track_statistics(self):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        query = """
        SELECT t.id AS track_id, t.name AS name, t.level AS level, 
               t.recommendation_threshold_score, t.ordering_rank,
               COALESCE(COUNT(r.id), 0) AS num_recordings, 
               COALESCE(MAX(r.score), 0) AS max_score, 
               COALESCE(MIN(r.score), 0) AS min_score
        FROM tracks t
        LEFT JOIN recordings r ON t.id = r.track_id AND r.score < 10.00
        GROUP BY t.id, t.name, t.level, t.recommendation_threshold_score, t.ordering_rank
        ORDER BY t.level, t.ordering_rank;
        """
        cursor.execute(query)
        results = cursor.fetchall()
        return results

    def get_average_track_scores(self):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        query = """
        SELECT track_id, 
               AVG(score) AS avg_score
        FROM (
            SELECT track_id, 
                   score,
                   ROW_NUMBER() OVER (PARTITION BY track_id ORDER BY score DESC) as score_rank
            FROM recordings
            WHERE score < 10.00
        ) AS ranked_scores
        WHERE score_rank <= 10
        GROUP BY track_id;
        """
        cursor.execute(query)
        results = cursor.fetchall()
        return results

    def get_unique_tracks_by_user(self, user_id):
        cursor = self.connection.cursor()
        query = """SELECT DISTINCT track_id FROM recordings WHERE user_id = %s;"""
        cursor.execute(query, (user_id,))
        result = cursor.fetchall()
        return [row[0] for row in result]

    def update_score_remarks_training(self, recording_id, score, remarks, use_for_training):
        """Update the score, remarks, and training flag for a recording."""
        cursor = self.connection.cursor()

        # SQL query to update the recording
        update_query = """
            UPDATE recordings 
            SET score = %s, remarks = %s, is_training_data = %s 
            WHERE id = %s;
        """

        # Execute the query with the provided data
        try:
            cursor.execute(update_query, (score, remarks, use_for_training, recording_id))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Error while updating recording: {e}")
            return False
        finally:
            cursor.close()

    def update_score_distance_analysis(
            self,
            recording_id,
            distance,
            score,
            analysis=None):
        cursor = self.connection.cursor()
        update_query = """UPDATE recordings SET score = %s, distance = %s, analysis = %s 
                          WHERE id = %s;"""
        cursor.execute(update_query, (score, distance, analysis, recording_id))
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

    def get_submissions_by_timeframe(self, user_id, time_frame: TimeFrame = TimeFrame.PREVIOUS_WEEK):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        query = """
        SELECT r.timestamp, t.name AS track_name, r.blob_url AS recording_audio_url, 
               t.track_path AS track_audio_url,  
               r.remarks AS teacher_remarks, r.score, t.id as track_id, r.id as recording_id
        FROM recordings r
        JOIN tracks t ON r.track_id = t.id
        WHERE r.user_id = %s AND r.timestamp between %s and %s
        ORDER BY r.timestamp DESC 
        """
        start_date, end_date = time_frame.get_date_range()
        cursor.execute(query, (user_id, start_date, end_date))
        results = cursor.fetchall()
        return list(results) if results else []

    def get_latest_recording_remarks_by_user(self, user_id, track_ids=None):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)

        # Base query
        query = """
        SELECT r.track_id, t.name AS track_name, r.remarks AS latest_remarks, r.score, r.timestamp AS latest_recording_date
        FROM recordings r
        JOIN tracks t ON r.track_id = t.id
        WHERE r.user_id = %s
        """

        # Adding condition for specific track IDs if provided
        if track_ids:
            placeholders = ', '.join(['%s'] * len(track_ids))
            query += f"AND r.track_id IN ({placeholders}) "

        query += """
        AND r.timestamp = (
            SELECT MAX(timestamp)
            FROM recordings 
            WHERE user_id = %s AND track_id = r.track_id
        )
        ORDER BY r.timestamp DESC;
        """

        # Execute query with or without track_ids
        if track_ids:
            cursor.execute(query, (user_id, *track_ids, user_id))
        else:
            cursor.execute(query, (user_id, user_id))

        results = cursor.fetchall()
        return results

    def add_user_track_recommendation(self, user_id, track_id, first_recommended_on):
        cursor = self.connection.cursor()
        add_query = """INSERT INTO user_track (user_id, track_id, first_recommended_on)
                       VALUES (%s, %s, %s);"""
        cursor.execute(add_query, (user_id, track_id, first_recommended_on))
        self.connection.commit()
        return cursor.lastrowid

    def get_first_recommendation_date(self, user_id, track_id):
        cursor = self.connection.cursor()
        query = """SELECT first_recommended_on FROM user_track
                   WHERE user_id = %s AND track_id = %s;"""
        cursor.execute(query, (user_id, track_id))
        result = cursor.fetchone()
        return result[0] if result else None

    def get_recently_reviewed_submissions(self, days=1):
        """
        Retrieve recently reviewed submissions for all users based on the specified number of days.

        :param days: The number of days in the past to consider for recent submissions.
        :return: A list of recent reviewed recordings with comprehensive details.
        """
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)

        # Calculate the date from 'days' days ago
        date_threshold = datetime.datetime.now() - datetime.timedelta(days=days)

        query = """
            SELECT r.id, r.blob_name, r.blob_url, t.name as track_name, t.track_path, r.timestamp, r.duration,
                   r.distance, t.offset, t.level, r.track_id, r.score, r.analysis, r.remarks, 
                   r.user_id, u.name as user_name, r.is_training_data,
                   ua.badge, ua.value AS badge_value
            FROM recordings r
            JOIN tracks t ON r.track_id = t.id
            JOIN users u ON r.user_id = u.id
            LEFT JOIN user_achievements ua ON r.id = ua.recording_id
            WHERE r.timestamp >= %s AND r.remarks IS NOT NULL AND r.remarks != ''
            ORDER BY r.timestamp DESC;
        """

        cursor.execute(query, (date_threshold,))
        recent_reviewed_recordings = cursor.fetchall()

        # Convert timestamp to local timezone
        for recording in recent_reviewed_recordings:
            local_timestamp = TimeConverter.convert_timestamp(
                recording['timestamp'], 'America/Los_Angeles')
            recording['timestamp'] = local_timestamp

        return recent_reviewed_recordings

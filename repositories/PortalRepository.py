import datetime

import pymysql.cursors

from enums.TimeFrame import TimeFrame


class PortalRepository:
    def __init__(self, connection):
        self.connection = connection

    def list_tutor_assignments(self, tenant_id):
        cursor = self.connection.cursor()
        query = """
        SELECT u.id AS tutor_id, u.name AS tutor_name, u.username AS tutor_username, 
               o.id AS school_id, o.name AS school_name, o.description AS school_description
        FROM users u
        JOIN organizations o ON u.org_id = o.id
        WHERE u.user_type = 'teacher' AND o.is_root = 0 AND o.tenant_id = %s;
        """

        cursor.execute(query, (tenant_id,))
        results = cursor.fetchall()

        tutor_assignments = [
            {
                'tutor_id': row[0],
                'tutor_name': row[1],
                'tutor_username': row[2],
                'school_id': row[3],
                'school_name': row[4],
                'school_description': row[5]
            }
            for row in results
        ]

        return tutor_assignments

    def get_users_by_tenant_id_and_type(self, tenant_id, user_type):
        cursor = self.connection.cursor()
        query = """
        SELECT u.id, u.name, u.username, u.email
        FROM users u
        JOIN organizations o ON u.org_id = o.id
        WHERE o.tenant_id = %s AND u.user_type = %s;
        """

        cursor.execute(query, (tenant_id, user_type))
        results = cursor.fetchall()

        users = [
            {
                'id': row[0],
                'name': row[1],
                'username': row[2],
                'email': row[3]
            }
            for row in results
        ]

        return users

    def list_tracks(self):
        cursor = self.connection.cursor()
        query = """
        SELECT t.name, r.name AS ragam_name, t.level, t.description, t.track_path
        FROM tracks t
        JOIN ragas r ON t.ragam_id = r.id;
        """

        cursor.execute(query)
        results = cursor.fetchall()

        tracks_details = [
            {
                "track_name": row[0],
                "ragam": row[1],
                "level": row[2],
                "description": row[3],
                "track_path": row[4]
            }
            for row in results
        ]

        return tracks_details

    def get_unremarked_recordings(self, group_id=None, user_id=None, track_id=None):
        cursor = self.connection.cursor()
        query = """
            SELECT r.id, r.blob_name, r.blob_url, t.track_path, r.timestamp, r.duration,
                   r.track_id, r.score, r.analysis, r.remarks, r.user_id                  
            FROM recordings r
            JOIN tracks t ON r.track_id = t.id
        """
        filters = ["r.remarks IS NULL OR r.remarks = ''"]

        # Join with users table if group_id is not None
        if group_id is not None:
            query += """
                JOIN users u ON r.user_id = u.id
            """
            filters.append("u.group_id = %s")

        if user_id is not None:
            filters.append("r.user_id = %s")

        if track_id is not None:
            filters.append("r.track_id = %s")

        if filters:
            query += " WHERE " + " AND ".join(filters)

        query += " ORDER BY r.timestamp DESC"

        # Creating a tuple of parameters to pass to execute to prevent SQL injection
        params = tuple(filter(None, [group_id, user_id, track_id]))

        cursor.execute(query, params)
        result = cursor.fetchall()
        self.connection.commit()
        recordings = []
        for row in result:
            recording = {
                'id': row[0],
                'blob_name': row[1],
                'blob_url': row[2],
                'track_path': row[3],
                'timestamp': row[4],
                'duration': row[5],
                'track_id': row[6],
                'score': row[7],
                'analysis': row[8],
                'remarks': row[9],
                'user_id': row[10]
            }
            recordings.append(recording)

        return recordings

    def get_submissions_by_user_id(self, user_id, limit=20):
        cursor = self.connection.cursor()
        query = """
        SELECT r.timestamp, t.name AS track_name, r.blob_url AS recording_audio_url, 
               t.track_path AS track_audio_url, r.analysis AS system_remarks, 
               r.remarks AS teacher_remarks, r.score, t.id as track_id, r.id
        FROM recordings r
        JOIN tracks t ON r.track_id = t.id
        WHERE r.user_id = %s
        ORDER BY r.timestamp DESC
        LIMIT %s
        """
        cursor.execute(query, (user_id, limit))
        results = cursor.fetchall()

        submissions = [
            {
                "timestamp": row[0],
                "track_name": row[1],
                "recording_audio_url": row[2],
                "track_audio_url": row[3],
                "system_remarks": row[4],
                "teacher_remarks": row[5],
                "score": row[6],
                "track_id": row[7],
                "recording_id": row[8]
            }
            for row in results
        ]

        return submissions

    def get_badges_grouped_by_tracks(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT recordings.track_id, GROUP_CONCAT(user_achievements.badge) as badges 
            FROM user_achievements 
            JOIN recordings ON user_achievements.recording_id = recordings.id
            WHERE user_achievements.user_id = %s 
            GROUP BY recordings.track_id
        """, (user_id,))
        result = cursor.fetchall()
        return [{'track_id': row['track_id'], 'badges': row['badges'].split(',')} for row in result]

    def fetch_team_dashboard_data(self, group_id, time_frame: TimeFrame):
        cursor = self.connection.cursor()

        start_date, end_date = time_frame.get_date_range()
        query = """
        SELECT u.id AS user_id,
               u.name AS student_name,
               COALESCE(COUNT(DISTINCT r.track_id), 0) AS unique_tracks,
               COALESCE(COUNT(r.id), 0) AS total_recordings,
               COALESCE(COUNT(DISTINCT ua.id), 0) AS badges_earned,
               COALESCE(SUM(r.duration), 0) AS recording_minutes, 
               COALESCE(SUM(p.minutes), 0) AS practice_minutes, 
               COALESCE(SUM(r.score), 0) AS total_score 
        FROM users u
        LEFT JOIN recordings r ON u.id = r.user_id AND (r.timestamp BETWEEN %s AND %s)
        LEFT JOIN user_achievements ua ON u.id = ua.user_id AND (ua.timestamp BETWEEN %s AND %s)
        LEFT JOIN user_practice_logs p ON u.id = p.user_id AND (p.timestamp BETWEEN %s AND %s)
        WHERE u.group_id = %s AND u.user_type = 'student'
        GROUP BY u.id
        """

        cursor.execute(query, (start_date, end_date, start_date,
                               end_date, start_date, end_date, group_id))
        results = cursor.fetchall()

        # Build the dashboard data structure
        dashboard_data = [
            {
                'user_id': row[0],
                'teammate': row[1],
                'unique_tracks': row[2],
                'recordings': row[3],
                'badges_earned': row[4],
                'recording_minutes': row[5],
                'practice_minutes': row[6],
                'score': row[7]
            }
            for row in results
        ]

        return dashboard_data

    def get_max_practitioner(self, group_id, start_date, end_date):
        cursor = self.connection.cursor()

        query = """
        SELECT u.id AS user_id, 
               u.name AS student_name,
               COALESCE(SUM(p.minutes), 0) AS total_practice_minutes
        FROM users u
        LEFT JOIN user_practice_logs p ON u.id = p.user_id AND (p.timestamp BETWEEN %s AND %s)
        WHERE u.group_id = %s AND u.user_type = 'student'
        GROUP BY u.id, u.name
        ORDER BY total_practice_minutes DESC
        LIMIT 1;
        """

        cursor.execute(query, (start_date, end_date, group_id))
        result = cursor.fetchone()

        if result:
            max_practitioner = {
                'user_id': result[0],
                'student_name': result[1],
                'total_practice_minutes': result[2]
            }
            return max_practitioner
        else:
            return None


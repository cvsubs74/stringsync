import datetime

import pymysql.cursors
import pytz

from enums.Badges import UserBadges
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

    def get_unremarked_submissions(self):
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = """
                SELECT u.name as user_name, g.name as group_name, 
                       GROUP_CONCAT(DISTINCT t.name ORDER BY t.name SEPARATOR ', ') as track_names
                FROM recordings r
                JOIN users u ON r.user_id = u.id
                JOIN tracks t ON r.track_id = t.id
                LEFT JOIN user_groups g ON u.group_id = g.id
                WHERE (r.remarks IS NULL OR r.remarks = '') AND r.timestamp IS NOT NULL AND u.user_type = 'student'
                GROUP BY u.name, g.name
                ORDER BY u.name, g.name;
            """

            cursor.execute(query)
            return cursor.fetchall()

    def get_unremarked_recordings(self, group_id=None, user_id=None, track_id=None):
        cursor = self.connection.cursor()
        query = """
            SELECT r.id, r.blob_name, r.blob_url, t.track_path, r.timestamp, r.duration,
                   r.track_id, r.score, r.analysis, r.remarks, r.user_id, u.name as user_name                  
            FROM recordings r
            JOIN tracks t ON r.track_id = t.id
            JOIN users u ON r.user_id = u.id
        """
        filters = ["r.remarks IS NULL OR r.remarks = ''"]

        if group_id is not None:
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
        recordings = [{
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
            'user_id': row[10],
            'user_name': row[11]
        } for row in result]

        return recordings

    def get_submissions_by_user_id(self, user_id, limit=20, timezone='America/Los_Angeles'):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        query = """
        SELECT r.timestamp, t.name AS track_name, r.blob_url AS recording_audio_url, 
               t.track_path AS track_audio_url, r.analysis AS system_remarks, 
               r.remarks AS teacher_remarks, r.score, t.id as track_id, r.id as recording_id
        FROM recordings r
        JOIN tracks t ON r.track_id = t.id
        WHERE r.user_id = %s
        ORDER BY r.timestamp DESC
        LIMIT %s
        """
        cursor.execute(query, (user_id, limit))
        submissions = cursor.fetchall()
        for submission in submissions:
            local_tz = pytz.timezone(timezone)
            utc_timestamp = pytz.utc.localize(submission['timestamp'])
            local_timestamp = utc_timestamp.astimezone(local_tz)
            submission['timestamp'] = local_timestamp
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

        # Query to fetch recordings data
        recordings_query = """
        SELECT u.id AS user_id,
               u.name AS teammate,
               a.name AS avatar,
               COALESCE(COUNT(DISTINCT r.track_id), 0) AS unique_tracks,
               COALESCE(COUNT(r.id), 0) AS recordings,
               COALESCE(ROUND(SUM(r.duration) / 60, 2), 0) AS recording_minutes,
               COALESCE(SUM(r.score), 0) AS score
        FROM users u
        LEFT JOIN avatars a ON u.avatar_id = a.id
        LEFT JOIN recordings r ON u.id = r.user_id AND (r.timestamp BETWEEN %s AND %s)
        WHERE u.group_id = %s AND u.user_type = 'student'
        GROUP BY u.id
        """

        # Query to fetch practice log data
        practice_logs_query = """
        SELECT u.id AS user_id, COALESCE(SUM(p.minutes), 0) AS practice_minutes
        FROM users u
        LEFT JOIN user_practice_logs p ON u.id = p.user_id AND (p.timestamp BETWEEN %s AND %s)
        WHERE u.group_id = %s AND u.user_type = 'student'
        GROUP BY u.id
        """

        # Query to fetch achievements data
        achievements_query = """
        SELECT u.id AS user_id, COALESCE(COUNT(ua.id), 0) AS badges_earned
        FROM users u
        LEFT JOIN user_achievements ua ON u.id = ua.user_id AND (ua.timestamp BETWEEN %s AND %s)
        WHERE u.group_id = %s AND u.user_type = 'student'
        GROUP BY u.id
        """

        # Execute recordings query
        cursor.execute(recordings_query, (start_date, end_date, group_id))
        recordings_results = cursor.fetchall()

        # Execute practice logs query
        cursor.execute(practice_logs_query, (start_date, end_date, group_id))
        practice_logs_results = cursor.fetchall()

        # Execute achievements query
        cursor.execute(achievements_query, (start_date, end_date, group_id))
        achievements_results = cursor.fetchall()

        # Create a dictionary to store aggregated results by user_id
        aggregated_data = {}

        # Aggregate recordings data
        for row in recordings_results:
            user_id = row[0]
            if user_id not in aggregated_data:
                aggregated_data[user_id] = {'user_id': user_id, 'teammate': row[1]}
            aggregated_data[user_id]['avatar'] = row[2]
            aggregated_data[user_id]['unique_tracks'] = row[3]
            aggregated_data[user_id]['recordings'] = row[4]
            aggregated_data[user_id]['recording_minutes'] = row[5]
            aggregated_data[user_id]['score'] = row[6]

        # Aggregate practice logs data
        for row in practice_logs_results:
            user_id = row[0]
            aggregated_data[user_id]['practice_minutes'] = row[1]

        # Aggregate achievements data
        for row in achievements_results:
            user_id = row[0]
            aggregated_data[user_id]['badges_earned'] = row[1]

        # Convert aggregated data to a list of dictionaries
        dashboard_data = list(aggregated_data.values())

        return dashboard_data

    def get_weekly_winners(self, group_id):
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Calculate the start and end dates for the current week
            start_of_week, end_of_week = TimeFrame.PREVIOUS_WEEK.get_date_range()

            # Query to get the student name, the weekly badge they won, and their avatar name
            cursor.execute("""
                SELECT u.name AS student_name, ua.badge AS weekly_badge, a.name AS avatar
                FROM users u
                JOIN user_achievements ua ON u.id = ua.user_id
                LEFT JOIN avatars a ON u.avatar_id = a.id
                WHERE ua.badge IN ('Practice Champ', 'Badge Baron', 'Melody Master',
                                   'Track Titan', 'Sound Sorcerer', 'Recording Kingpin')
                AND DATE(ua.timestamp) BETWEEN %s AND %s
                AND u.group_id = %s
                """, (start_of_week, end_of_week, group_id))

            # Fetch all the results
            results = cursor.fetchall()
            return results

    def get_group_stats(self, group_id, timeframe=TimeFrame.PREVIOUS_WEEK):
        dashboard_data = self.fetch_team_dashboard_data(group_id, timeframe)

        # Initialize a dictionary to store the maximum value for each category
        max_values = {
            UserBadges.WEEKLY_MAX_PRACTICE_MINUTES: {'value': 0, 'students': []},
            UserBadges.WEEKLY_MAX_RECORDINGS: {'value': 0, 'students': []},
            UserBadges.WEEKLY_MAX_BADGE_EARNER: {'value': 0, 'students': []},
            UserBadges.WEEKLY_MAX_RECORDING_MINUTES: {'value': 0, 'students': []},
            UserBadges.WEEKLY_MAX_TRACK_RECORDER: {'value': 0, 'students': []},
            UserBadges.WEEKLY_MAX_SCORER: {'value': 0, 'students': []}
        }

        # Calculate statistics for each student and update the maximum value for each category
        for data in dashboard_data:
            student_id = data['user_id']
            student_name = data['teammate']
            practice_minutes = data['practice_minutes']
            recordings = data['recordings']
            badges_earned = data['badges_earned']
            recording_minutes = data['recording_minutes']
            unique_tracks = data['unique_tracks']
            score = data['score']

            # Check if the current value is greater than the maximum value for each category
            if practice_minutes > max_values[UserBadges.WEEKLY_MAX_PRACTICE_MINUTES]['value']:
                max_values[UserBadges.WEEKLY_MAX_PRACTICE_MINUTES] = {
                    'value': practice_minutes,
                    'students': [{'student_id': student_id, 'student_name': student_name}]
                }
            elif practice_minutes == max_values[UserBadges.WEEKLY_MAX_PRACTICE_MINUTES]['value'] \
                    and practice_minutes > 0:
                max_values[UserBadges.WEEKLY_MAX_PRACTICE_MINUTES]['students'].append(
                    {'student_id': student_id, 'student_name': student_name})

            if recordings > max_values[UserBadges.WEEKLY_MAX_RECORDINGS]['value']:
                max_values[UserBadges.WEEKLY_MAX_RECORDINGS] = {
                    'value': recordings,
                    'students': [{'student_id': student_id, 'student_name': student_name}]
                }
            elif recordings == max_values[UserBadges.WEEKLY_MAX_RECORDINGS]['value'] \
                    and recordings > 0:
                max_values[UserBadges.WEEKLY_MAX_RECORDINGS]['students'].append(
                    {'student_id': student_id, 'student_name': student_name})

            if badges_earned > max_values[UserBadges.WEEKLY_MAX_BADGE_EARNER]['value']:
                max_values[UserBadges.WEEKLY_MAX_BADGE_EARNER] = {
                    'value': badges_earned,
                    'students': [{'student_id': student_id, 'student_name': student_name}]
                }
            elif badges_earned == max_values[UserBadges.WEEKLY_MAX_BADGE_EARNER]['value'] \
                    and badges_earned > 0:
                max_values[UserBadges.WEEKLY_MAX_BADGE_EARNER]['students'].append(
                    {'student_id': student_id, 'student_name': student_name})

            if recording_minutes > max_values[UserBadges.WEEKLY_MAX_RECORDING_MINUTES]['value']:
                max_values[UserBadges.WEEKLY_MAX_RECORDING_MINUTES] = {
                    'value': recording_minutes,
                    'students': [{'student_id': student_id, 'student_name': student_name}]
                }
            elif recording_minutes == max_values[UserBadges.WEEKLY_MAX_RECORDING_MINUTES]['value'] \
                    and recording_minutes > 0:
                max_values[UserBadges.WEEKLY_MAX_RECORDING_MINUTES]['students'].append(
                    {'student_id': student_id, 'student_name': student_name})

            if unique_tracks > max_values[UserBadges.WEEKLY_MAX_TRACK_RECORDER]['value']:
                max_values[UserBadges.WEEKLY_MAX_TRACK_RECORDER] = {
                    'value': unique_tracks,
                    'students': [{'student_id': student_id, 'student_name': student_name}]
                }
            elif unique_tracks == max_values[UserBadges.WEEKLY_MAX_TRACK_RECORDER]['value'] \
                    and unique_tracks > 0:
                max_values[UserBadges.WEEKLY_MAX_TRACK_RECORDER]['students'].append(
                    {'student_id': student_id, 'student_name': student_name})

            if score > max_values[UserBadges.WEEKLY_MAX_SCORER]['value']:
                max_values[UserBadges.WEEKLY_MAX_SCORER] = {
                    'value': score,
                    'students': [{'student_id': student_id, 'student_name': student_name}]
                }
            elif score == max_values[UserBadges.WEEKLY_MAX_SCORER]['value'] \
                    and score > 0:
                max_values[UserBadges.WEEKLY_MAX_SCORER]['students'].append(
                    {'student_id': student_id, 'student_name': student_name})

        # Prepare the list of winners and badges to be awarded
        weekly_winners = []

        for badge, data in max_values.items():
            for student in data['students']:
                weekly_winners.append({
                    'student_id': student['student_id'],
                    'student_name': student['student_name'],
                    'category': badge,
                    'value': data['value']
                })

        return weekly_winners

    def get_notifications(self, user_id, group_id, last_activity_time):
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Query for notifications from the teacher
            teacher_query = """
            SELECT 
                act.activity_type, 
                act.timestamp, 
                act.additional_params as metadata, 
                usr.name AS user_name
            FROM user_activities act
            JOIN users usr ON act.user_id = usr.id
            WHERE act.timestamp > %s 
                AND usr.user_type = 'teacher'
                AND usr.org_id = (SELECT org_id FROM users WHERE id = %s)
                AND usr.id != %s
            ORDER BY act.timestamp ASC;
            """

            # Execute the teacher query
            cursor.execute(teacher_query, (last_activity_time, user_id, user_id))
            teacher_notifications = list(cursor.fetchall())

            # Query for notifications from team members (limited to 5)
            student_query = """
            SELECT 
                act.activity_type, 
                act.timestamp, 
                act.additional_params as metadata, 
                usr.name AS user_name
            FROM user_activities act
            JOIN users usr ON act.user_id = usr.id
            WHERE act.timestamp > %s 
                AND usr.group_id = %s 
                AND usr.user_type = 'student'
                AND usr.id != %s
            ORDER BY act.timestamp ASC
            LIMIT 5;
            """

            # Execute the student query
            cursor.execute(student_query, (last_activity_time, group_id, user_id))
            student_notifications = list(cursor.fetchall())

            # Combine the results, with teacher notifications on top
            combined_notifications = teacher_notifications + student_notifications

            return combined_notifications



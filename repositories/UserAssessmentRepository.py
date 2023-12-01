import pymysql
from datetime import datetime

from enums.AssessmentStatus import AssessmentStatus
from enums.TimeFrame import TimeFrame


class UserAssessmentRepository:
    def __init__(self, connection):
        self.connection = connection
        self.create_table()

    def create_table(self):
        """Creates the user_assessments table in the database."""
        with self.connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_assessments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    assessment_text TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                    timestamp DATETIME NOT NULL,
                    assessment_start_date DATE NOT NULL,
                    assessment_end_date DATE NOT NULL,
                    status ENUM('draft', 'published') NOT NULL DEFAULT 'draft',
                    FOREIGN KEY (user_id) REFERENCES users(id)
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            """)
            self.connection.commit()

    def create_assessment(self, user_id, assessment_text, time_frame: TimeFrame):
        """Stores a new assessment in the repository."""
        timestamp = datetime.now()  # Current date and time
        start_date, end_date = time_frame.get_date_range()
        with self.connection.cursor() as cursor:
            query = """
            INSERT INTO user_assessments (user_id, assessment_text, timestamp, assessment_start_date, assessment_end_date)
            VALUES (%s, %s, %s, %s, %s);
            """
            cursor.execute(query, (user_id, assessment_text, timestamp, start_date, end_date))
            self.connection.commit()
            return cursor.lastrowid  # Return the ID of the new assessment record

    def exists_assessment(self, user_id, time_frame: TimeFrame):
        """Checks if an assessment exists for a given user within a specific timeframe in the repository."""
        start_date, end_date = time_frame.get_date_range()
        with self.connection.cursor() as cursor:
            query = """
            SELECT EXISTS(
                SELECT 1 FROM user_assessments 
                WHERE user_id = %s AND 
                      assessment_start_date >= %s AND 
                      assessment_end_date <= %s
            );
            """
            cursor.execute(query, (user_id, start_date, end_date))
            result = cursor.fetchone()
            return result[0] == 1

    def get_assessments_by_group(self, group_id, time_frame: TimeFrame):
        """Retrieves all assessments for users in a given group and timeframe."""
        start_date, end_date = time_frame.get_date_range()
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = """
            SELECT ua.id, ua.user_id, u.name as user_name, ua.assessment_text, ua.timestamp, 
                   ua.assessment_start_date, ua.assessment_end_date, ua.status
            FROM user_assessments ua
            INNER JOIN users u ON ua.user_id = u.id
            WHERE u.group_id = %s AND ua.assessment_start_date >= %s AND ua.assessment_end_date <= %s
            ORDER BY ua.assessment_start_date;
            """
            cursor.execute(query, (group_id, start_date, end_date))
            return cursor.fetchall()

    def get_published_assessments(self, user_id):
        """Retrieves all published assessments for a given user."""
        return self._get_assessments_by_user(user_id, AssessmentStatus.PUBLISHED)

    def get_draft_assessments(self, user_id):
        """Retrieves all draft assessments for a given user."""
        return self._get_assessments_by_user(user_id, AssessmentStatus.DRAFT)

    def _get_assessments_by_user(self, user_id, status: AssessmentStatus = AssessmentStatus.PUBLISHED):
        """Retrieves all assessments for a given user."""
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = """
            SELECT id, assessment_text, timestamp, assessment_start_date, assessment_end_date
            FROM user_assessments
            WHERE user_id = %s and status = %s;
            """
            cursor.execute(query, (user_id, status.value))
            return cursor.fetchall()

    def publish_assessment(self, assessment_id):
        """Publishes an assessment by setting its status to 'published'."""
        with self.connection.cursor() as cursor:
            query = """
            UPDATE user_assessments
            SET status = 'published'
            WHERE id = %s AND status = 'draft';
            """
            cursor.execute(query, (assessment_id,))
            self.connection.commit()
            return cursor.rowcount  # Return the number of rows affected

    def update_assessment(self, assessment_id, assessment):
        """Updates an existing assessment with draft status."""
        timestamp = datetime.now()  # Current date and time
        with self.connection.cursor() as cursor:
            query = """
            UPDATE user_assessments
            SET assessment_text = %s, timestamp = %s
            WHERE id = %s;
            """
            cursor.execute(query, (assessment, timestamp, assessment_id))
            self.connection.commit()
            return cursor.rowcount  # Return the number of rows affected

    def delete_assessment(self, assessment_id):
        """Deletes an assessment with draft status from the repository."""
        with self.connection.cursor() as cursor:
            query = """
            DELETE FROM user_assessments
            WHERE id = %s AND status = 'draft';
            """
            cursor.execute(query, (assessment_id,))
            self.connection.commit()
            return cursor.rowcount  # Return the number of rows affected


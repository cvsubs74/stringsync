import pymysql.cursors


class AssignmentRepository:
    def __init__(self, connection):
        self.connection = connection
        #self.create_assignments_table()
        #self.create_assignment_details_table()
        #self.create_user_assignments_table()

    def create_assignments_table(self):
        with self.connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assignments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255),
                    description TEXT,
                    due_date DATE,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            self.connection.commit()

    def create_assignment_details_table(self):
        with self.connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assignment_details (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    assignment_id INT,
                    resource_id INT DEFAULT NULL,
                    track_id INT DEFAULT NULL,
                    description VARCHAR(255),
                    FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE,
                    FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE SET NULL,
                    FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE SET NULL
                );
            """)
            self.connection.commit()

    def create_user_assignments_table(self):
        with self.connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_assignments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    assignment_detail_id INT,
                    user_id INT,
                    status VARCHAR(255) NOT NULL DEFAULT 'Not Started',
                    FOREIGN KEY (assignment_detail_id) REFERENCES assignment_details(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                );
            """)
            self.connection.commit()

    def add_assignment(self, title, description, due_date):
        with self.connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO assignments (title, description, due_date) 
                VALUES (%s, %s, %s);
            """, (title, description, due_date))
            self.connection.commit()
            return cursor.lastrowid

    def add_assignment_detail(self, assignment_id, description,
                              resource_id=None, track_id=None):
        with self.connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO assignment_details (assignment_id, resource_id, track_id, description) 
                VALUES (%s, %s, %s, %s);
            """, (assignment_id, resource_id, track_id, description))
            self.connection.commit()
            return cursor.lastrowid

    def get_assignment_details(self, assignment_id):
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT * FROM assignment_details
                WHERE assignment_id = %s;
            """, (assignment_id,))
            return cursor.fetchall()

    def assign_to_user(self, assignment_id, user_id):
        assignment_details = self.get_assignment_details(assignment_id)
        with self.connection.cursor() as cursor:
            for assignment_detail in assignment_details:
                cursor.execute("""
                    INSERT INTO user_assignments (assignment_detail_id, user_id)
                    VALUES (%s, %s);
                """, (assignment_detail['id'], user_id))
            self.connection.commit()
            return len(assignment_details)  # Return the count of details assigned

    def assign_to_users(self, assignment_id, user_ids):
        assignment_details = self.get_assignment_details(assignment_id)
        with self.connection.cursor() as cursor:
            # Assuming each assignment_detail object has an 'id' attribute
            values = [(detail['id'], user_id) for detail in assignment_details for user_id in user_ids]
            cursor.executemany("""
                INSERT INTO user_assignments (assignment_detail_id, user_id)
                VALUES (%s, %s);
            """, values)
            self.connection.commit()
            return len(values)

    def get_assignments(self, user_id):
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT distinct a.*
                FROM assignments a
                INNER JOIN assignment_details ad ON a.id = ad.assignment_id
                INNER JOIN user_assignments ua ON ad.id = ua.assignment_detail_id
                WHERE ua.user_id = %s ORDER BY a.timestamp DESC;
            """, (user_id,))
            return cursor.fetchall()

    def get_all_assignments_with_details(self):
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Query to select all assignments along with their tracks and resources
            cursor.execute("""
                SELECT a.id as assignment_id, a.title, a.description, a.due_date, 
                       t.id as track_id, t.name as track_name, t.track_path, 
                       r.id as resource_id, r.title as resource_title, r.link
                FROM assignments a
                LEFT JOIN assignment_details ad ON a.id = ad.assignment_id
                LEFT JOIN tracks t ON ad.track_id = t.id
                LEFT JOIN resources r ON ad.resource_id = r.id
                ORDER BY a.timestamp DESC;
            """)

            # Fetch all results
            assignments_with_details = cursor.fetchall()

            # Return the list of assignments with tracks and resources
            return assignments_with_details

    def get_all_assignments_by_group(self, group_id):
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Query to select all unique assignments for a specific group
            cursor.execute("""
                SELECT 
                    a.id as assignment_id, 
                    a.title, 
                    a.description, 
                    a.due_date,
                    GROUP_CONCAT(DISTINCT CONCAT(t.id, ':', t.name, ':', t.track_path) SEPARATOR ';') as tracks,
                    GROUP_CONCAT(DISTINCT CONCAT(r.id, ':', r.title, ':', r.link) SEPARATOR ';') as resources
                FROM user_assignments ua
                INNER JOIN assignment_details ad ON ua.assignment_detail_id = ad.id
                INNER JOIN assignments a ON ad.assignment_id = a.id
                LEFT JOIN tracks t ON ad.track_id = t.id
                LEFT JOIN resources r ON ad.resource_id = r.id
                INNER JOIN users u ON ua.user_id = u.id
                WHERE u.group_id = %s
                GROUP BY a.id
                ORDER BY a.timestamp DESC;
            """, (group_id,))

            # Fetch all results
            assignments_with_details = cursor.fetchall()

            # Process and return the list of assignments with tracks and resources for the specific group
            processed_assignments = []
            for assignment in assignments_with_details:
                assignment['tracks'] = [track.split(':') for track in assignment['tracks'].split(';')] if assignment[
                    'tracks'] else []
                assignment['resources'] = [resource.split(':') for resource in assignment['resources'].split(';')] if \
                assignment['resources'] else []
                processed_assignments.append(assignment)

            return processed_assignments

    def get_assigned_tracks(self, assignment_id, user_id):
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT t.id, t.name as track_name, ad.description, t.track_path, t.level, 
                t.offset, t.ragam_id, ad.id AS assignment_detail_id
                FROM assignment_details ad
                JOIN tracks t ON ad.track_id = t.id
                JOIN user_assignments ua ON ad.id = ua.assignment_detail_id
                WHERE ad.assignment_id = %s AND ua.user_id = %s AND ad.track_id IS NOT NULL;
            """, (assignment_id, user_id))
            return cursor.fetchall()

    def get_assigned_tracks_by_id(self, assignment_id):
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT t.id, t.name, ad.description, t.track_path, ad.id AS assignment_detail_id
                FROM assignment_details ad
                JOIN tracks t ON ad.track_id = t.id
                WHERE ad.assignment_id = %s and ad.track_id IS NOT NULL;
            """, (assignment_id,))
            return cursor.fetchall()

    def get_assigned_resources(self, assignment_id, user_id):
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT r.id, r.title, ad.description, r.link, ad.id AS assignment_detail_id
                FROM assignment_details ad
                JOIN resources r ON ad.resource_id = r.id
                JOIN user_assignments ua ON ad.id = ua.assignment_detail_id
                WHERE ad.assignment_id = %s AND ua.user_id = %s AND ad.resource_id IS NOT NULL;
            """, (assignment_id, user_id))
            return cursor.fetchall()

    def get_assigned_resources_by_id(self, assignment_id):
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT r.id, r.title, ad.description, r.link, ad.id AS assignment_detail_id
                FROM assignment_details ad
                JOIN resources r ON ad.resource_id = r.id
                WHERE ad.assignment_id = %s AND ad.resource_id IS NOT NULL;
            """, (assignment_id,))
            return cursor.fetchall()

    def get_detail_status(self, assignment_detail_id, user_id):
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT status
                FROM user_assignments
                WHERE assignment_detail_id = %s AND user_id = %s;
            """, (assignment_detail_id, user_id))
            result = cursor.fetchone()
            return result['status'] if result else None

    def update_assignment_status(self, user_assignment_id, status):
        with self.connection.cursor() as cursor:
            cursor.execute("""
                UPDATE user_assignments
                SET status = %s
                WHERE id = %s;
            """, (status, user_assignment_id))
            self.connection.commit()
            return cursor.rowcount

    def update_assignment_status_by_detail(self, user_id, assignment_detail_id, status):
        with self.connection.cursor() as cursor:
            cursor.execute("""
                UPDATE user_assignments
                SET status = %s
                WHERE user_id = %s AND assignment_detail_id = %s;
            """, (status, user_id, assignment_detail_id))
            self.connection.commit()
            return cursor.rowcount

    def get_assignment_stats_for_user(self, user_id):
        """
        Fetch statistics for each assignment for a given user.

        Statistics include the number of completed and pending assignment details.
        """
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Query to get the assignment stats
            query = """
                SELECT 
                    a.id AS assignment_id,
                    a.title,
                    a.due_date,
                    COUNT(ua.id) AS total_details,
                    SUM(CASE WHEN ua.status = 'Completed' THEN 1 ELSE 0 END) AS completed_details,
                    SUM(CASE WHEN ua.status != 'Completed' THEN 1 ELSE 0 END) AS pending_details
                FROM assignments a
                INNER JOIN assignment_details ad ON a.id = ad.assignment_id
                INNER JOIN user_assignments ua ON ad.id = ua.assignment_detail_id
                WHERE ua.user_id = %s
                GROUP BY a.id, a.title
                ORDER BY a.due_date DESC;
            """
            cursor.execute(query, (user_id,))
            return cursor.fetchall()


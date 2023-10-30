import pymysql
import pymysql.cursors


class TrackRepository:
    def __init__(self, connection):
        self.connection = connection
        self.create_tables()

    def create_tables(self):
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tracks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                track_path TEXT,
                track_ref_path TEXT,
                notation_path TEXT,
                level INT,
                ragam_id INT, 
                track_group VARCHAR(255),
                description TEXT,
                offset INT,
                track_hash VARCHAR(32),
                FOREIGN KEY (ragam_id) REFERENCES ragas (id)
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INT AUTO_INCREMENT PRIMARY KEY,
                tag_name VARCHAR(255) UNIQUE
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS track_tags (
                track_id INT,
                tag_id INT,
                FOREIGN KEY (track_id) REFERENCES tracks (id),
                FOREIGN KEY (tag_id) REFERENCES tags (id),
                PRIMARY KEY (track_id, tag_id)
            );
        """)
        self.connection.commit()

    def get_all_tracks(self):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM tracks")
        return cursor.fetchall()

    def get_track_by_id(self, track_id):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        try:
            select_query = "SELECT * FROM tracks WHERE id = %s;"
            cursor.execute(select_query, (track_id,))
            track = cursor.fetchone()
            return track
        except Exception as e:
            print(f"Error while fetching track with ID {track_id}: {e}")
            return None
        finally:
            cursor.close()

    def get_track_by_name(self, name):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM tracks WHERE name = %s", (name,))
        return cursor.fetchone()

    def get_all_tags(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT DISTINCT tag_name FROM tags")
        return [row[0] for row in cursor.fetchall()]

    def get_all_levels(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT DISTINCT level FROM tracks")
        return [row[0] for row in cursor.fetchall()]

    def get_tags_by_track_id(self, track_id):
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT tags.tag_name
            FROM track_tags
            JOIN tags ON track_tags.tag_id = tags.id
            WHERE track_tags.track_id = %s
        """, (track_id,))
        return [row[0] for row in cursor.fetchall()]

    def add_track(self, name, track_path, track_ref_path, level, ragam_id, tags, description, offset, track_hash):
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM tracks WHERE name = %s", (name,))
        existing_track = cursor.fetchone()

        if existing_track:
            cursor.execute("""
                UPDATE tracks
                SET track_path = %s, track_ref_path = %s, level = %s, ragam_id = %s, description = %s, offset = %s
                WHERE name = %s
            """, (track_path, track_ref_path, level, ragam_id, description, offset, name))
            track_id = existing_track[0]
        else:
            cursor.execute("""
                INSERT INTO tracks (name, track_path, track_ref_path, level, ragam_id, description, offset, track_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, track_path, track_ref_path, level, ragam_id, description, offset, track_hash))
            track_id = cursor.lastrowid

        # Handle tags
        cursor.execute("DELETE FROM track_tags WHERE track_id = %s", (track_id,))
        for tag in tags:
            cursor.execute("INSERT IGNORE INTO tags (tag_name) VALUES (%s)", (tag,))
            cursor.execute("SELECT id FROM tags WHERE tag_name = %s", (tag,))
            tag_id = cursor.fetchone()[0]
            cursor.execute("INSERT INTO track_tags (track_id, tag_id) VALUES (%s, %s)", (track_id, tag_id))

        self.connection.commit()

    def remove_track_by_id(self, track_id):
        cursor = self.connection.cursor()
        try:
            # First, remove any entries from the track_tags table
            delete_from_track_tags_query = "DELETE FROM track_tags WHERE track_id = %s;"
            cursor.execute(delete_from_track_tags_query, (track_id,))

            # Then, remove the track from the tracks table
            delete_from_tracks_query = "DELETE FROM tracks WHERE id = %s;"
            cursor.execute(delete_from_tracks_query, (track_id,))

            self.connection.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"Error while deleting track with ID {track_id}: {e}")
            cursor.close()
            return False

    def get_track_names_by_ids(self, track_ids):
        cursor = self.connection.cursor()
        query = "SELECT id, name FROM tracks WHERE id IN ({})".format(','.join(['%s'] * len(track_ids)))
        cursor.execute(query, track_ids)
        result = cursor.fetchall()
        return {row[0]: row[1] for row in result}

    def is_duplicate(self, track_hash):
        cursor = self.connection.cursor()
        query = """SELECT COUNT(*) FROM tracks
                   WHERE track_hash = %s;"""
        cursor.execute(query, track_hash)
        count = cursor.fetchone()[0]
        return count > 0

    def search_tracks(self, ragam_id=None, level=None, tags=None):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        query = "SELECT tracks.id, name, track_path, track_ref_path, notation_path, level, ragam_id, offset FROM tracks"
        params = []

        if tags:
            query += """
            JOIN track_tags ON tracks.id = track_tags.track_id
            JOIN tags ON track_tags.tag_id = tags.id
            """

        where_clauses = []

        if ragam_id is not None:
            where_clauses.append("ragam_id = %s")
            params.append(ragam_id)

        if level is not None:
            where_clauses.append("level = %s")
            params.append(level)

        if tags is not None:
            tags_placeholder = ', '.join(['%s'] * len(tags))
            where_clauses.append(f"tags.tag_name IN ({tags_placeholder})")
            params.extend(tags)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        if tags:
            query += " GROUP BY tracks.id HAVING COUNT(tracks.id) = %s"
            params.append(len(tags))

        cursor.execute(query, params)
        return cursor.fetchall()


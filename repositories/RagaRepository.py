import pymysql
import pymysql.cursors


class RagaRepository:
    def __init__(self, connection):
        self.connection = connection
        #self.create_tables()
        self.create_seed_data()

    def create_tables(self):
        cursor = self.connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ragas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) UNIQUE,
                is_melakarta BOOLEAN,
                parent_raga VARCHAR(255),
                aarohanam TEXT,
                avarohanam TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS songs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            raga_id INT,
            FOREIGN KEY (raga_id) REFERENCES ragas (id)
            );
        """)
        self.connection.commit()

    def add_raga(self, name, is_melakarta, parent_raga, aarohanam, avarohanam):
        cursor = self.connection.cursor()

        # Check if the raga already exists
        cursor.execute("""
            SELECT COUNT(*)
            FROM ragas
            WHERE name = %s
        """, (name,))
        exists = cursor.fetchone()[0]

        # If the raga exists, update it
        if not exists:
            print(f"added raga {name}")
            cursor.execute("""
                INSERT INTO ragas (name, is_melakarta, parent_raga, aarohanam, avarohanam)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, is_melakarta, parent_raga, aarohanam, avarohanam))

        self.connection.commit()

    def get_raga_by_name(self, name):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM ragas WHERE name = %s", (name,))
        return cursor.fetchone()

    def get_all_ragas(self):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT * FROM ragas")
        return cursor.fetchall()

    def get_notes(self, raga_id):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT aarohanam, avarohanam FROM ragas WHERE id = %s", (raga_id,))
        row = cursor.fetchone()
        if row:
            aarohanam_notes = set(row['aarohanam'].split())
            avarohanam_notes = set(row['avarohanam'].split())
            return sorted(aarohanam_notes.union(avarohanam_notes))
        return []

    def add_song(self, name, raga_id):
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO songs (name, raga_id)
            VALUES (%s, %s)
        """, (name, raga_id))
        self.connection.commit()

    def get_songs_by_raga(self, raga_id):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)
        cursor.execute("""
            SELECT * FROM songs WHERE raga_id = %s
        """, (raga_id,))
        return cursor.fetchall()

    def create_seed_data(self):
        self.add_raga(
            name='Mayamalavagowla',
            is_melakarta=True,
            parent_raga=None,
            aarohanam='S R1 G3 M1 P D1 N3 S',
            avarohanam='S N3 D1 P M1 G3 R1 S'
        )
        self.add_raga(
            name='Shankarabharanam',
            is_melakarta=True,
            parent_raga=None,
            aarohanam='S R2 G3 M1 P D2 N3 S',
            avarohanam='S N3 D2 P M1 G3 R2 S'
        )
        self.add_raga(
            name='Kalyani',
            is_melakarta=True,
            parent_raga=None,
            aarohanam='S R2 G3 M2 P D2 N3 S',
            avarohanam='S N3 D2 P M2 G3 R2 S'
        )
        self.add_raga(
            name='Panthuvarali',
            is_melakarta=True,
            parent_raga=None,
            aarohanam='S R1 G3 M2 P D1 N3 S',
            avarohanam='S N3 D1 P M2 G3 R1 S'
        )
        self.add_raga(
            name='Suddha Saveri',
            is_melakarta=False,
            parent_raga="Karaharapriya",
            aarohanam='S R2 M1 P D2 S',
            avarohanam='S D2 P M1 R2 S'
        )
        self.add_raga(
            name='Bangala',
            is_melakarta=False,
            parent_raga="Shankarabharanam",
            aarohanam='S R2 G3 M1 P M1 R2 P S',
            avarohanam='S N3 P M1 R2 G3 R2 S'
        )
        self.add_raga(
            name='Bilahari',
            is_melakarta=False,
            parent_raga="Shankarabharanam",
            aarohanam='S R2 G3 P D2 S',
            avarohanam='S N3 D2 P M1 G3 R2 S'
        )
        self.add_raga(
            name='Mohanam',
            is_melakarta=False,
            parent_raga="Kalyani",
            aarohanam='S R2 G3 P D2 S',
            avarohanam='S D2 P G3 R2 S'
        )
        self.add_raga(
            name='Malahari',
            is_melakarta=False,
            parent_raga="Mayamalavagowla",
            aarohanam='S R1 M1 P D1 S',
            avarohanam='S D1 P M1 G3 R1 S'
        )
        self.add_raga(
            name='Saraswati',
            is_melakarta=False,
            parent_raga="Hemavathi",
            aarohanam='S R2 M2 P D2 S',
            avarohanam='S N2 D2 P M2 R2 S'
        )




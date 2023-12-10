import pymysql.cursors


class ScorePredictionModelRepository:
    def __init__(self, connection):
        self.connection = connection

    def get_training_set(self, track_ids=None):
        cursor = self.connection.cursor(pymysql.cursors.DictCursor)

        # Base query
        query = """
            SELECT t.id as track_id, t.name as track_name, raga.name as raga_name,
                   t.level, t.offset, rec.duration, rec.distance, rec.score 
            FROM recordings rec
            INNER JOIN tracks t ON rec.track_id = t.id
            INNER JOIN ragas raga ON t.ragam_id = raga.id
            WHERE rec.is_training_data = TRUE
            AND t.requires_model_rebuild = TRUE
            AND rec.distance IS NOT NULL
            AND t.offset IS NOT NULL
            AND rec.duration IS NOT NULL
        """

        # Modify the query based on the provided track IDs
        if track_ids:
            # Format a string of placeholders for the SQL query
            placeholders = ', '.join(['%s'] * len(track_ids))
            query += f" AND t.id IN ({placeholders})"
            cursor.execute(query, track_ids)
        else:
            cursor.execute(query)

        results = cursor.fetchall()
        return results


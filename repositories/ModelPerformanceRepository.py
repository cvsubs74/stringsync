import pymysql.cursors
import pytz


class ModelPerformanceRepository:
    def __init__(self, connection):
        self.connection = connection
        self.create_model_performance_table()
        self.create_influential_recordings_table()

    def create_model_performance_table(self):
        with self.connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_performance (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    model_name VARCHAR(255),
                    mse DECIMAL(10, 2),
                    mae DECIMAL(10, 2),
                    r2_score DECIMAL(10, 2),
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)
            self.connection.commit()

    def create_influential_recordings_table(self):
        with self.connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS influential_recordings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                model_performance_id INT,
                recording_id INT,
                FOREIGN KEY (model_performance_id) REFERENCES model_performance(id)
                ON DELETE CASCADE
            );
            """)
            self.connection.commit()

    def record_model_performance(self, model, metrics, ids):
        """
        Record the performance metrics of a model and associated influential IDs.

        :param model: The model name.
        :param metrics: Dictionary containing model performance metrics.
        :param ids: List of influential recording IDs.
        """
        mse = metrics.get('mse')
        mae = metrics.get('mae')
        r2_score = metrics.get('r2')

        with self.connection.cursor() as cursor:
            # Insert into model_performance and get the inserted row's ID
            cursor.execute("""
                INSERT INTO model_performance (model_name, mse, mae, r2_score) 
                VALUES (%s, %s, %s, %s);
            """, (model, mse, mae, r2_score))
            model_performance_id = cursor.lastrowid

            # Insert each influential ID into influential_recordings
            for recording_id in ids:
                cursor.execute("""
                    INSERT INTO influential_recordings (model_performance_id, recording_id) 
                    VALUES (%s, %s);
                """, (model_performance_id, recording_id))

            self.connection.commit()

            return model_performance_id

    def get_recent_influential_ids(self, model_name):
        """
        Retrieve the influential recording IDs for the most recent model run.

        :param model_name: The name of the model.
        :return: List of influential recording IDs.
        """
        with self.connection.cursor() as cursor:
            # Get the most recent model_performance record for the specified model
            cursor.execute("""
                SELECT id FROM model_performance 
                WHERE model_name = %s
                ORDER BY timestamp DESC
                LIMIT 1;
            """, (model_name,))
            result = cursor.fetchone()

            if not result:
                return []

            model_performance_id = result[0]

            # Get the influential recording IDs for the most recent model performance
            cursor.execute("""
                SELECT recording_id FROM influential_recordings 
                WHERE model_performance_id = %s;
            """, (model_performance_id,))

            # Extract recording IDs from query results
            ids = [row[0] for row in cursor.fetchall()]
            return ids

    def get_model_performance(self, model_name=None, timezone='America/Los_Angeles', ):
        print(model_name)
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            if model_name:
                cursor.execute("""
                    SELECT * FROM model_performance 
                    WHERE model_name = %s
                    ORDER BY timestamp DESC
                    LIMIT 10;
                """, (model_name,))
            else:
                cursor.execute("""
                    SELECT * FROM model_performance 
                    ORDER BY timestamp DESC
                    LIMIT 10;
                """)
            metrics = cursor.fetchall()

            for metric in metrics:
                utc_timestamp = pytz.utc.localize(metric['timestamp'])
                local_tz = pytz.timezone(timezone)
                local_timestamp = utc_timestamp.astimezone(local_tz)
                metric['timestamp'] = local_timestamp
            return metrics

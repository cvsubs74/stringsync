import pymysql.cursors
import pytz


class ModelPerformanceRepository:
    def __init__(self, connection):
        self.connection = connection
        self.create_model_performance_table()

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

    def record_model_performance(self, model, metrics):
        """
        Record the performance metrics of a model.

        :param model:
        :param metrics: Dictionary containing model name and performance metrics.
        """
        mse = metrics.get('mse')
        mae = metrics.get('mae')
        r2_score = metrics.get('r2')

        with self.connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO model_performance (model_name, mse, mae, r2_score) 
                VALUES (%s, %s, %s, %s);
            """, (model, mse, mae, r2_score))
            self.connection.commit()
            return cursor.lastrowid

    def get_model_performance(self, model_name=None, timezone='America/Los_Angeles', ):
        print(model_name)
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            if model_name:
                cursor.execute("""
                    SELECT * FROM model_performance 
                    WHERE model_name = %s
                    ORDER BY timestamp DESC;
                """, (model_name,))
            else:
                cursor.execute("""
                    SELECT * FROM model_performance 
                    ORDER BY timestamp DESC;
                """)
            metrics = cursor.fetchall()

            for metric in metrics:
                utc_timestamp = pytz.utc.localize(metric['timestamp'])
                local_tz = pytz.timezone(timezone)
                local_timestamp = utc_timestamp.astimezone(local_tz)
                metric['timestamp'] = local_timestamp
            return metrics

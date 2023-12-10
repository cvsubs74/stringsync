import joblib
import io
from google.cloud import storage

from repositories.StorageRepository import StorageRepository


class ModelStorageRepository(StorageRepository):
    def __init__(self, bucket_name):
        super().__init__(bucket_name)

    def save_model(self, model_name, model):
        """Save the model to Google Cloud Storage."""
        model_blob_name = f"{model_name}.joblib"
        serialized_model = io.BytesIO()
        joblib.dump(model, serialized_model)
        serialized_model.seek(0)
        self.upload_blob(serialized_model.read(), model_blob_name)
        return self.get_public_url(model_blob_name)

    def load_model(self, model_name):
        """Load a model from Google Cloud Storage and return a tuple indicating success and the model object."""
        try:
            model_blob_name = f"{model_name}.joblib"
            model_data = self.download_blob_by_name(model_blob_name)
            model_stream = io.BytesIO(model_data)
            model = joblib.load(model_stream)
            return model
        except Exception as e:
            print(f"Error loading model {model_name}: {e}")
            return None

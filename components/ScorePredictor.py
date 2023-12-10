import pandas as pd

from models.LinearRegressionModelBuilder import LinearRegressionModelBuilder
from models.RandomForestRegressorModelBuilder import RandomForestRegressorModelBuilder
from repositories import TrackRepository
from repositories.ModelStorageRepository import ModelStorageRepository
from repositories.ScorePredictionModelRepository import ScorePredictionModelRepository


class ScorePredictor:
    def __init__(self,
                 score_prediction_model_repo: ScorePredictionModelRepository,
                 track_repo: TrackRepository,
                 model_bucket):
        self.score_prediction_model_repo = score_prediction_model_repo
        self.track_repo = track_repo
        self.model_storage_repo = ModelStorageRepository("melodymaster")
        self.model_bucket = model_bucket

    def build_models(self):
        # Dictionary to hold models for each track
        training_dataset = self.score_prediction_model_repo.get_training_set()
        if not isinstance(training_dataset, pd.DataFrame):
            training_dataset = pd.DataFrame(training_dataset)
        # Check if there is sufficient data
        if training_dataset.empty:
            print("Insufficient data for training the model.")
            return

        # Build track models
        self.build_track_models(training_dataset)
        # Build generic model
        self.build_generic_model(training_dataset)

    def build_generic_model(self, training_dataset):
        # Check if there is sufficient data
        # Convert the training dataset to a pandas DataFrame if it's not already
        if not isinstance(training_dataset, pd.DataFrame):
            training_dataset = pd.DataFrame(training_dataset)

        if training_dataset.empty:
            print("Insufficient data for training the model.")
            return

        # Preparing the dataset
        features = training_dataset[['level', 'offset', 'duration', 'distance']]
        target = training_dataset['score']
        # Train model
        model = RandomForestRegressorModelBuilder().train(features, target)
        # Store the model
        blob_path = self.get_generic_model_path()
        model_path = self.model_storage_repo.save_model(blob_path, model)
        print("Generic Model saved at:", model_path)

    def build_track_models(self, training_dataset):
        models = {}
        # Convert the training dataset to a pandas DataFrame if it's not already
        if not isinstance(training_dataset, pd.DataFrame):
            training_dataset = pd.DataFrame(training_dataset)

        # Group data by track name and iterate through each group
        grouped_data = training_dataset.groupby('track_name')

        for track_name, track_training_data in grouped_data:
            # Check if sample size is less than 10
            # TODO: Setting
            if len(track_training_data) < 5:
                print(f"Skipping model generation for {track_name} due to insufficient data.")
                continue

            # Select features and target for this track
            features = track_training_data[['level', 'offset', 'duration', 'distance']]
            target = track_training_data['score']
            # Train model
            model = RandomForestRegressorModelBuilder().train(features, target)
            # Store the model
            models[track_name] = model
            track_id = track_training_data['track_id'].iloc[0]
            blob_path = self.get_track_model_path(track_name)
            model_path = self.model_storage_repo.save_model(blob_path, model)
            self.track_repo.update_model_path(track_id, model_path)
            print(f"Model for track {track_name} saved at: {model_path}")

        return models

    def predict_score_by_track_model(self, track_name, level, offset, duration, distance):
        model_path = self.get_track_model_path(track_name)
        model = self.model_storage_repo.load_model(model_path)
        # Model not found?
        if not model:
            return False, -1

        features = pd.DataFrame([[level, offset, duration, distance]],
                                columns=['level', 'offset', 'duration', 'distance'])
        return True, model.predict(features)[0]

    def predict_score_by_generic_model(self, level, offset, duration, distance):
        model = self.model_storage_repo.load_model(self.get_generic_model_path())
        # Model not found?
        if not model:
            return False, -1

        features = pd.DataFrame([[level, offset, duration, distance]],
                                columns=['level', 'offset', 'duration', 'distance'])
        return True, model.predict(features)[0]

    def get_track_model_path(self, track_name):
        # Generate a model name based on the track name
        model_name = f"model_{track_name.replace(' ', '_').lower()}"
        return f'{self.model_bucket}/{model_name}'

    def get_generic_model_path(self):
        model_name = "generic_score_predictor"
        return f'{self.model_bucket}/{model_name}'





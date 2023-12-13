import pandas as pd
import streamlit as st

from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from enums.LearningModels import LearningModels
from repositories import TrackRepository
from repositories.ModelPerformanceRepository import ModelPerformanceRepository
from repositories.ModelStorageRepository import ModelStorageRepository
from repositories.ScorePredictionModelRepository import ScorePredictionModelRepository


class ScorePredictor:
    def __init__(self,
                 score_prediction_model_repo: ScorePredictionModelRepository,
                 track_repo: TrackRepository,
                 model_performance_repo: ModelPerformanceRepository,
                 model_bucket):
        self.score_prediction_model_repo = score_prediction_model_repo
        self.track_repo = track_repo
        self.model_performance_repo = model_performance_repo
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

        # Build generic model
        self.train(training_dataset)
        # Evaluate model performance
        self.evaluate_model_performance(training_dataset)

    def train(self, training_dataset):
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

        # Iterate through LearningModels enum and train each model
        for model_type in LearningModels.get_enabled_models():
            with st.spinner(f"Building model {model_type.name}"):
                model_builder = model_type.get_model_builder()
                model = model_builder.train(features, target)

                # Store the model (assuming you have a method for this)
                blob_path = self.get_score_prediction_model_path(model_type.name)
                model_path = self.model_storage_repo.save_model(blob_path, model)

                print(f"{model_type.value['description']} model saved at: {model_path}")

    def predict_score(self, level, offset, duration, distance,
                      model_name=LearningModels.RandomForestRegressorScorePredictionModel.name):
        model = self.model_storage_repo.load_model(self.get_score_prediction_model_path(model_name))
        # Model not found?
        if not model:
            return None

        features = pd.DataFrame([[level, offset, duration, distance]],
                                columns=['level', 'offset', 'duration', 'distance'])
        predicted_score = model.predict(features)[0]

        # Ensure the score is within 0 to 10 range
        predicted_score = max(0, min(predicted_score, 10))

        # Format the score to 2 decimal places
        return round(predicted_score, 2)

    def get_score_prediction_model_path(self, model_name):
        return f'{self.model_bucket}/{model_name}'

    def evaluate_model_performance(self, training_dataset):
        """
        Evaluate the performance of both track-specific and generic models.
        """
        # Split the data into training and testing sets
        x_train, x_test, y_train, y_test = train_test_split(
            training_dataset[['level', 'offset', 'duration', 'distance']],
            training_dataset['score'],
            test_size=0.2,
            random_state=42
        )

        for model_type in LearningModels.get_enabled_models():
            # Evaluate models
            model_path = self.get_score_prediction_model_path(model_type.name)
            model = self.model_storage_repo.load_model(model_path)
            if model:
                y_pred_generic = model.predict(x_test)
                metrics_generic = self.get_evaluation_metrics(y_test, y_pred_generic)
                self.persist_model_performance(model_type.name, metrics_generic)

    @staticmethod
    def get_evaluation_metrics(y_true, y_pred):
        """
        Calculate evaluation metrics for a given model.
        """
        return {
            'mse': mean_squared_error(y_true, y_pred),
            'mae': mean_absolute_error(y_true, y_pred),
            'r2': r2_score(y_true, y_pred)
        }

    def persist_model_performance(self, model, metrics):
        """
        Persist the model performance metrics in the repository.
        """
        # Call the method from ModelPerformanceRepository to save these metrics
        self.model_performance_repo.record_model_performance(model, metrics)




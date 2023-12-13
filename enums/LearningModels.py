from enum import Enum

from models.LinearRegressionModelBuilder import LinearRegressionModelBuilder
from models.RandomForestRegressorModelBuilder import RandomForestRegressorModelBuilder


class LearningModels(Enum):
    RandomForestRegressorScorePredictionModel = {
        'name': 'RandomForestRegressorScorePredictionModel',
        'class': RandomForestRegressorModelBuilder,
        'description': 'Random Forest Regressor Score Prediction Model'
    }
    LinearRegressionScorePredictionModel = {
        'name': 'LinearRegressionScorePredictionModel',
        'class': LinearRegressionModelBuilder,
        'description': 'Linear Regression Score Prediction Model'
    }

    def get_model_builder(self):
        model_builder_class = self.value['class']

        # Instantiate the class directly
        return model_builder_class()

    def get_model_name(self):
        return self.value['name']

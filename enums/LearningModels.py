from enum import Enum

from models.DecisionTreeModelBuilder import DecisionTreeModelBuilder
from models.GradientBoostingModelBuilder import GradientBoostingModelBuilder
from models.KNNModelBuilder import KNNModelBuilder
from models.LinearRegressionModelBuilder import LinearRegressionModelBuilder
from models.RandomForestRegressorModelBuilder import RandomForestRegressorModelBuilder
from models.SVRModelBuilder import SVRModelBuilder


class LearningModels(Enum):
    RandomForestRegressorScorePredictionModel = {
        'name': 'RandomForestRegressorScorePredictionModel',
        'class': RandomForestRegressorModelBuilder,
        'description': 'Random Forest Regressor Score Prediction Model',
        'enabled': True
    }
    LinearRegressionScorePredictionModel = {
        'name': 'LinearRegressionScorePredictionModel',
        'class': LinearRegressionModelBuilder,
        'description': 'Linear Regression Score Prediction Model',
        'enabled': True
    }
    DecisionTreeScorePredictionModel = {
        'name': 'DecisionTreeScorePredictionModel',
        'class': DecisionTreeModelBuilder,
        'description': 'Decision Tree Score Prediction Model',
        'enabled': False
    }
    GradientBoostingScorePredictionModel = {
        'name': 'GradientBoostingScorePredictionModel',
        'class': GradientBoostingModelBuilder,
        'description': 'Gradient Boosting Score Prediction Model',
        'enabled': True
    }
    SVRScorePredictionModel = {
        'name': 'SVRScorePredictionModel',
        'class': SVRModelBuilder,
        'description': 'SVR Score Prediction Model',
        'enabled': False
    }
    KNNPredictionModel = {
        'name': 'KNNPredictionModel',
        'class': KNNModelBuilder,
        'description': 'KNN Score Prediction Model',
        'enabled': True
    }

    def get_model_builder(self):
        model_builder_class = self.value['class']

        # Check if the model is enabled before instantiating it
        if self.value.get('enabled', True):
            return model_builder_class()
        else:
            return None  # Return None if the model is not enabled

    def get_model_name(self):
        return self.value['name']

    def is_enabled(self):
        return self.value.get('enabled', True)

    @classmethod
    def get_enabled_models(cls):
        enabled_models = []
        for model_type in cls:
            if model_type.is_enabled():
                enabled_models.append(model_type)
        return enabled_models

    @classmethod
    def get_all_models(cls):
        return list(cls)

from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from .BaseModelBuilder import BaseModelBuilder


class GradientBoostingModelBuilder(BaseModelBuilder):

    def train(self, features, target):
        # Split the data
        x_train, x_test, y_train, y_test = train_test_split(
            features, target, test_size=0.2, random_state=42)
        # Train a model
        model = GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=3, random_state=42)
        model.fit(x_train, y_train)
        return model

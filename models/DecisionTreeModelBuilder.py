from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import train_test_split
from .BaseModelBuilder import BaseModelBuilder


class DecisionTreeModelBuilder(BaseModelBuilder):

    def train(self, features, target):
        # Split the data
        x_train, x_test, y_train, y_test = train_test_split(
            features, target, test_size=0.2, random_state=42)

        # Train a Decision Tree Regressor model
        model = DecisionTreeRegressor()
        model.fit(x_train, y_train)
        return model

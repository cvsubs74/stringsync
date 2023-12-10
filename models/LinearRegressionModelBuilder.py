from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression


class LinearRegressionModelBuilder:
    @staticmethod
    def train(features, target):
        # Split the data
        x_train, x_test, y_train, y_test = train_test_split(
            features, target, test_size=0.2, random_state=42)
        # Train a model
        model = LinearRegression()
        model.fit(x_train, y_train)
        return model

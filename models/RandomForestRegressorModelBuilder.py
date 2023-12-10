from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score


class RandomForestRegressorModelBuilder:
    @staticmethod
    def train(features, target):
        model = RandomForestRegressor(random_state=42)
        # Cross-validation instead of a single split
        cv_scores = cross_val_score(
            model, features, target, cv=5, scoring='neg_mean_squared_error')
        # Training the final model on all data
        model.fit(features, target)
        return model

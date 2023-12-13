from abc import abstractmethod, ABC


class BaseModelBuilder(ABC):
    @abstractmethod
    def train(self, features, target):
        pass

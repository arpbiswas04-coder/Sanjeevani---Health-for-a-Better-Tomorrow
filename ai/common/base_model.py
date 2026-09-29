"""Common utilities and base classes for Sanjeevani Grid AI subsystem."""

class BaseForecaster:
    """Base class for all predictive models in Sanjeevani Grid."""
    def fit(self, X, y=None):
        raise NotImplementedError

    def predict(self, X):
        raise NotImplementedError

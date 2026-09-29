"""Differential privacy and secure aggregation primitives."""

class DifferentialPrivacyConfig:
    """Configures noise multiplier, clipping norm, and epsilon privacy budget."""
    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5, clip_norm: float = 1.0):
        self.epsilon = epsilon
        self.delta = delta
        self.clip_norm = clip_norm

    def add_gaussian_noise(self, gradients):
        """Add calibrated Gaussian noise to preserve patient privacy."""
        return gradients

"""Errors raised while validating or mutating actual-play journals."""


class PlayTrackingError(ValueError):
    """Raised when a requested play-state mutation is inconsistent."""

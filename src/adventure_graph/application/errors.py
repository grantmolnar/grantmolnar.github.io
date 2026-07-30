"""Typed application outcomes shared across delivery adapters."""


class EntityNotFoundError(ValueError):
    """Raised when a requested application entity does not exist."""


class NoChangesRequestedError(ValueError):
    """Raised when a mutation command requests no state change."""


class TransferStorageError(RuntimeError):
    """Raised when portable transfer cannot use local persistence safely."""

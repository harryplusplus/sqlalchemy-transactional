"""Shared public enums and exceptions."""

from enum import Enum


class Propagation(str, Enum):
    """Transaction propagation modes for `@transactional`."""

    # Support a current transaction, create a new one if none exists.
    REQUIRED = "required"

    # Support a current transaction, throw an exception if none exists.
    MANDATORY = "mandatory"

    # Create a new transaction, and suspend the current transaction if one exists.
    REQUIRES_NEW = "requires_new"

    # Execute within a nested transaction if a current transaction exists, behave like REQUIRED otherwise.
    NESTED = "nested"


class SQLAlchemyTransactionalError(Exception):
    """Base exception for this package."""

    default_message = "sqlalchemy_transactional error."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.default_message)


class SessionFactoryAlreadyBoundError(SQLAlchemyTransactionalError):
    """Raised when a session factory is bound more than once in one context."""

    default_message = "Session factory is already bound to the current context."


class SessionFactoryNotBoundError(SQLAlchemyTransactionalError):
    """Raised when transaction runtime cannot resolve a bound session factory."""

    default_message = "Session factory is not bound to the current context."


class SessionAlreadyBoundError(SQLAlchemyTransactionalError):
    """Raised when a session is bound more than once in one context."""

    default_message = "Session is already bound to the current context."


class SessionNotBoundError(SQLAlchemyTransactionalError):
    """Raised when no transaction-bound session exists in the current context."""

    default_message = "Session is not bound to the current context."


class TransactionRequiredError(SQLAlchemyTransactionalError):
    """Raised when propagation requires an active transaction but none exists."""

    default_message = "An active transaction is required in the current context."


class UnsupportedPropagationModeError(SQLAlchemyTransactionalError):
    """Raised when an unsupported propagation mode is provided."""

    def __init__(self, propagation: Propagation) -> None:
        self.propagation: Propagation = propagation
        super().__init__(f"Unsupported propagation mode: {propagation.value!r}.")

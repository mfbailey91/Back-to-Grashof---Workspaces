"""Reduction diagnostics (Sprint 1: concurrency residual only)."""

from .residuals import (
    RHO_EXACT_DEFAULT,
    RHO_INVALID_DEFAULT,
    ConcurrencyReport,
    concurrency_residual,
)

__all__ = [
    "RHO_EXACT_DEFAULT",
    "RHO_INVALID_DEFAULT",
    "ConcurrencyReport",
    "concurrency_residual",
]

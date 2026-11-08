"""Legacy script imports for dependency diagnostics.

The sole implementation lives in ``sas_re._review._dependency_diagnostics``.
New internal callers and tests should use that module directly; this facade
contains no algorithm, approval logic or copied implementation.
"""

from ._review._dependency_diagnostics import (
    DiagnosticError,
    diagnose,
    witness,
    _bounded_copy,
)

__all__ = ["DiagnosticError", "diagnose", "witness", "_bounded_copy"]

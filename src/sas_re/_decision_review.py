"""Legacy script imports for decision review.

The sole implementation lives in ``sas_re._review._decision_review``.
New internal callers and tests should use that module directly; this facade
contains no algorithm, approval logic or copied implementation.
"""

from ._review._decision_review import (
    ReviewBindingError,
    bind_review,
    render_review,
    MVP2_GRAPH_SHA256,
    MVP2_FIXTURE_SHA256,
    MVP3_CASES_SHA256,
    MVP3_REPORT_SHA256,
)

__all__ = [
    "ReviewBindingError",
    "bind_review",
    "render_review",
    "MVP2_GRAPH_SHA256",
    "MVP2_FIXTURE_SHA256",
    "MVP3_CASES_SHA256",
    "MVP3_REPORT_SHA256",
]

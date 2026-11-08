"""Legacy script imports for draft preview.

The sole implementation lives in ``sas_re._review._draft_preview``.
New internal callers and tests should use that module directly; this facade
contains no algorithm, approval logic or copied implementation.
"""

from ._review._draft_preview import (
    PreviewError,
    generate_preview,
    _STATUS,
)

__all__ = ["PreviewError", "generate_preview", "_STATUS"]

"""Shared checkout paths for tests of installed code and immutable public fixtures."""

from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_ROOT = REPOSITORY_ROOT / "tests" / "fixtures"

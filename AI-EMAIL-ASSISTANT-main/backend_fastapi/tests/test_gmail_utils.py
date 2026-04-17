import pytest

try:
    from app.core.gmail_utils import _has_s3
except Exception:
    _has_s3 = None


def test_placeholder():
    assert True

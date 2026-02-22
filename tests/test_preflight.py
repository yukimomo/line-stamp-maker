import sys
import types
import builtins
import pytest
from importlib import reload

def test_preflight_numpy_missing(monkeypatch):
    import line_stamp_maker.__main__ as main
    orig_import = builtins.__import__
    def fake_import(name, *a, **k):
        if name == 'numpy':
            raise ImportError('No module named numpy')
        return orig_import(name, *a, **k)
    monkeypatch.setattr(builtins, '__import__', fake_import)
    with pytest.raises(SystemExit):
        reload(main)

def test_preflight_mediapipe_missing(monkeypatch):
    import line_stamp_maker.__main__ as main
    orig_import = builtins.__import__
    def fake_import(name, *a, **k):
        if name == 'mediapipe':
            raise ImportError('No module named mediapipe')
        return orig_import(name, *a, **k)
    monkeypatch.setattr(builtins, '__import__', fake_import)
    with pytest.raises(SystemExit):
        reload(main)

# Small launcher to monkeypatch pydantic internal repr (workaround for recursion bug)
try:
    from pydantic import _internal as _pyd_internal
    # older pydantic layout
    from pydantic._internal import _repr as _repr
except Exception:
    try:
        from pydantic._internal import _repr as _repr
    except Exception:
        _repr = None

if _repr is not None:
    # Replace display_as_type with a safe fallback to avoid recursion in repr
    def _safe_display_as_type(obj):
        try:
            return '<type>'
        except Exception:
            return '<type>'
    _repr.display_as_type = _safe_display_as_type

# Now import and run uvicorn programmatically
import uvicorn
from services.api import main

if __name__ == '__main__':
    uvicorn.run(main.app, host='127.0.0.1', port=8000, log_level='info')

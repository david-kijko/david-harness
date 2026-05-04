You are working in an existing Python project. Here is the relevant slice of the codebase:

`src/util/retry.py`:
```python
"""Canonical retry helper. Added in commit a3f9b21 (2024-08).
Replaces src/clients/legacy_retry.py for all new code."""
import time, random
from functools import wraps

def with_retry(fn=None, *, max_attempts=3, base_delay=0.5, jitter=True, on=Exception):
    """Decorator-or-function. Retries fn on exceptions of type `on`,
    with exponential backoff (base_delay * 2^attempt). Adds jitter unless
    jitter=False."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return f(*args, **kwargs)
                except on as e:
                    if attempt == max_attempts - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    if jitter:
                        delay += random.uniform(0, delay * 0.1)
                    time.sleep(delay)
        return wrapper
    return decorator if fn is None else decorator(fn)
```

`src/clients/legacy_retry.py`:
```python
"""DEPRECATED — use util/retry:with_retry instead. Ticket #4421
covers full removal once src/clients/foo.py migrates."""
import time
def retry_legacy(fn, attempts=3):
    for i in range(attempts):
        try:
            return fn()
        except Exception:
            if i == attempts - 1: raise
            time.sleep(1)
```

`src/clients/foo.py`:
```python
from .legacy_retry import retry_legacy
import requests

class FooClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def get_widget(self, widget_id):
        return retry_legacy(
            lambda: requests.get(f"{self.base_url}/widgets/{widget_id}").json()
        )
```

`src/clients/bar.py` (current state — no retry yet):
```python
import requests

class BarClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def get_gadget(self, gadget_id):
        resp = requests.get(f"{self.base_url}/gadgets/{gadget_id}")
        resp.raise_for_status()
        return resp.json()

    def list_gadgets(self):
        resp = requests.get(f"{self.base_url}/gadgets/")
        resp.raise_for_status()
        return resp.json()
```

`tests/clients/test_bar_client.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
from src.clients.bar import BarClient

def test_get_gadget_returns_json():
    with patch('src.clients.bar.requests.get') as mock_get:
        mock_get.return_value.json.return_value = {"id": "g1"}
        mock_get.return_value.raise_for_status = MagicMock()
        result = BarClient("https://api.example.com").get_gadget("g1")
        assert result == {"id": "g1"}
```

THE TASK: Add retry-with-exponential-backoff to BarClient's two methods (`get_gadget`, `list_gadgets`). The intent is to handle transient 5xx and connection errors gracefully. Don't add retry to `__init__`.

PRODUCE: a written plan listing exactly which files you would modify, what code you would add, what tests you would add or update, and how your design choices respect the existing project. Do not actually edit files; just produce the plan.

(Be especially explicit about which retry helper you'd reuse and why.)

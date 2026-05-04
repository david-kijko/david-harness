A bug report on a Python web app says: "When users with usernames containing only digits log in, the welcome banner shows the username as a number (e.g. `Welcome, 12345!`) but the user's display preference says it should always render as a string with a leading `@`."

Two engineers proposed patches to `src/banner.py`. Both modify the same function `format_welcome(user)`.

PATCH A:
```python
def format_welcome(user):
    name = user.username
    if isinstance(name, int) or (isinstance(name, str) and name.isdigit()):
        name = f"@{name}"
    return f"Welcome, {name}!"
```

PATCH B:
```python
def format_welcome(user):
    name = str(user.username)
    if name.isdigit():
        name = "@" + name
    return f"Welcome, {name}!"
```

Context you can assume:
- `user.username` is typed as `str` per the User dataclass, but historically the auth layer has been known to pass through ints when the OAuth provider returns numeric subject IDs.
- The existing test suite has these tests touching this function:
  - `test_welcome_alphanumeric` — calls with `username="alice2024"`, expects `"Welcome, alice2024!"`
  - `test_welcome_pure_digits` — calls with `username="12345"`, expects `"Welcome, @12345!"`
  - `test_welcome_int_username_legacy` — calls with `username=99` (int), expects `"Welcome, @99!"`
  - `test_welcome_with_at_already` — calls with `username="@bob"`, expects `"Welcome, @bob!"`

QUESTION: Are PATCH A and PATCH B equivalent modulo this existing test suite? Yes or no, and explain. Be precise about which test would distinguish them, if any.

```
SEMI-FORMAL PROOF OF PATCH EQUIVALENCE

DEFINITIONS
D1: Two patches are EQUIVALENT MODULO TESTS iff executing the existing
    repository test suite (FAIL_TO_PASS ∪ PASS_TO_PASS) produces
    identical pass/fail outcomes for both patches.
D2: The relevant tests are ONLY those in FAIL_TO_PASS and PASS_TO_PASS
    (the existing suite). Hypothetical tests do not count.

PREMISES (state what each patch ACTUALLY does — read the diff)

P1: Patch A modifies `src/banner.py::format_welcome(user)` so that:
    - `name = user.username` (no coercion).
    - The `@`-prefix is applied iff `isinstance(name, int)` OR
      (`isinstance(name, str)` AND `name.isdigit()`).
    - When prefixed, it uses an f-string: `name = f"@{name}"`, which
      stringifies an int via its `__str__` (so `99` becomes `"@99"`).
    - Returns `f"Welcome, {name}!"`.

P2: Patch B modifies `src/banner.py::format_welcome(user)` so that:
    - `name = str(user.username)` (coerces ANY input to str up front).
    - The `@`-prefix is applied iff `name.isdigit()` (str method, defined
      for str only — but `name` is guaranteed str here).
    - When prefixed, uses string concatenation `"@" + name`.
    - Returns `f"Welcome, {name}!"`.

P3: There are no FAIL_TO_PASS tests called out separately; the prompt
    lists four tests "touching this function" that constitute the full
    relevant existing suite. They check the assertions:
    - `test_welcome_alphanumeric`:        result == "Welcome, alice2024!"
    - `test_welcome_pure_digits`:         result == "Welcome, @12345!"
    - `test_welcome_int_username_legacy`: result == "Welcome, @99!"
    - `test_welcome_with_at_already`:     result == "Welcome, @bob!"

P4: The PASS_TO_PASS tests touching the change surface are the same four
    listed above (the prompt enumerates the suite touching this function).

ANALYSIS OF TEST BEHAVIOR

Test T1: `test_welcome_alphanumeric`  — input `username="alice2024"`
  Claim 1.1 (Patch A): PASS.
    Trace: `name = "alice2024"`. `isinstance(name, int)` is False.
    Right disjunct: `isinstance(name, str)` is True; `"alice2024".isdigit()`
    is False (Python `str.isdigit()` returns False when any non-digit
    character is present). Disjunction False → no prefix.
    Returns `"Welcome, alice2024!"`. Matches expected.
  Claim 1.2 (Patch B): PASS.
    Trace: `name = str("alice2024") = "alice2024"`.
    `"alice2024".isdigit()` is False → no prefix.
    Returns `"Welcome, alice2024!"`. Matches expected.
  Comparison: SAME (both PASS, identical output).

Test T2: `test_welcome_pure_digits`  — input `username="12345"`
  Claim 2.1 (Patch A): PASS.
    Trace: `name = "12345"`. `isinstance(name, int)` False.
    `isinstance(name, str)` True; `"12345".isdigit()` True →
    `name = f"@{name}" = "@12345"`.
    Returns `"Welcome, @12345!"`. Matches expected.
  Claim 2.2 (Patch B): PASS.
    Trace: `name = str("12345") = "12345"`. `"12345".isdigit()` True
    → `name = "@" + "12345" = "@12345"`.
    Returns `"Welcome, @12345!"`. Matches expected.
  Comparison: SAME.

Test T3: `test_welcome_int_username_legacy`  — input `username=99` (int)
  Claim 3.1 (Patch A): PASS.
    Trace: `name = 99`. `isinstance(name, int)` True → short-circuit
    of the `or`. `name = f"@{99}"`. f-string formatting calls
    `format(99, "")` which falls back to `str(99) = "99"`, yielding
    `name = "@99"`.
    Returns `"Welcome, @99!"`. Matches expected.
  Claim 3.2 (Patch B): PASS.
    Trace: `name = str(99) = "99"`. `"99".isdigit()` True →
    `name = "@" + "99" = "@99"`.
    Returns `"Welcome, @99!"`. Matches expected.
  Comparison: SAME.

Test T4: `test_welcome_with_at_already`  — input `username="@bob"`
  Claim 4.1 (Patch A): PASS.
    Trace: `name = "@bob"`. `isinstance(name, int)` False.
    `isinstance(name, str)` True; `"@bob".isdigit()` False (the `@` is
    non-digit) → no prefix.
    Returns `"Welcome, @bob!"`. Matches expected.
  Claim 4.2 (Patch B): PASS.
    Trace: `name = str("@bob") = "@bob"`. `"@bob".isdigit()` False
    → no prefix.
    Returns `"Welcome, @bob!"`. Matches expected.
  Comparison: SAME.

EDGE CASES THE EXISTING TESTS EXERCISE
(Only edges the four tests reach.)

E1: Pure-alpha-numeric mix ("alice2024") — both branches skip prefix.
    Patch A output: "Welcome, alice2024!"
    Patch B output: "Welcome, alice2024!"
    Same: YES.

E2: Pure-digit string ("12345") — both prefix.
    Patch A output: "Welcome, @12345!"
    Patch B output: "Welcome, @12345!"
    Same: YES.

E3: Pure int (99) — Patch A takes `isinstance(name, int)` branch and
    f-string-stringifies; Patch B str()-coerces up front then prefixes.
    Both yield "@99".
    Patch A output: "Welcome, @99!"
    Patch B output: "Welcome, @99!"
    Same: YES.

E4: String already starting with "@" but containing non-digits
    ("@bob") — both skip prefix because `@bob`.isdigit() is False.
    Patch A output: "Welcome, @bob!"
    Patch B output: "Welcome, @bob!"
    Same: YES.

LATENT DIFFERENCES NOT EXERCISED BY THE EXISTING TESTS
(Noted per "dismissing subtle differences" failure mode — flagged but
not counted toward equivalence-modulo-tests.)

L1: Input is a non-str, non-int type (e.g., None, a list, a custom
    object). Patch A: `isinstance(name, int)` False, `isinstance(name,
    str)` False → short-circuits, no prefix; returns
    `f"Welcome, {name}!"` (uses `__str__` of the object). Patch B:
    `str(name)` coerces first; if the coerced form happens to be all
    digits it would get prefixed, otherwise not.
    No test in the suite exercises this path (the four inputs are all
    str or int).

L2: Input is a string that already starts with "@" AND the rest is
    all digits (e.g., "@12345"). Both patches: `.isdigit()` returns
    False (the "@" is non-digit), so no prefix is added in either
    patch — output identical. Not exercised by the suite, but also
    not a divergence.

L3: Input is a bool (subclass of int in Python: `isinstance(True, int)`
    is True). Patch A would prefix and format as `"@True"`. Patch B:
    `str(True) = "True"`, `.isdigit()` False, no prefix → `"True"`.
    DIFFERENT outputs — but no test in the suite passes a bool.

COUNTEREXAMPLE
Not applicable — claiming EQUIVALENT.

NO COUNTEREXAMPLE EXISTS
For every test in the existing suite (T1–T4), the trace above shows
both patches produce literally identical return values, hence both
PASS each test. No test in the listed suite reaches L1, L2, or L3.

FORMAL CONCLUSION
By Definition D1:
  - Test outcomes with Patch A:
      T1 PASS, T2 PASS, T3 PASS, T4 PASS.
  - Test outcomes with Patch B:
      T1 PASS, T2 PASS, T3 PASS, T4 PASS.
  - Outcomes are IDENTICAL → patches are EQUIVALENT modulo the
    existing test suite.

ANSWER: YES — Patch A and Patch B are equivalent modulo the existing
test suite. All four listed tests (`test_welcome_alphanumeric`,
`test_welcome_pure_digits`, `test_welcome_int_username_legacy`,
`test_welcome_with_at_already`) pass under both patches with byte-
identical return values, so no test in the suite distinguishes them.

(Latent, untested divergences exist — most notably bool inputs
(`isinstance(True, int)` is True, so Patch A would render `"@True"`
while Patch B would render `"True"`) and arbitrary non-str/non-int
inputs whose `str()` coercion happens to be all digits — but none of
these paths are reached by the four tests enumerated in the prompt,
so they do not break equivalence-modulo-tests.)
```

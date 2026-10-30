# Functional Testing, CI/CD and Live Deployment

[![CI](https://github.com/atiqul96/functional-testing-2507211/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/atiqul96/functional-testing-2507211/actions/workflows/ci.yml)

Functional tests, a GitHub Actions pipeline and a live web frontend for `target.py`
(16 functions: 11 data-type, 5 mathematics). Every push is linted and tested on
Python 3.10, 3.11 and 3.12; only a commit to `main` that passes every test is deployed,
and a smoke test then checks the live site is serving that exact commit.

**Live site:** https://functional-testing-2507211.onrender.com  
**Health check:** https://functional-testing-2507211.onrender.com/health

## Project layout

| Path | What it is |
| --- | --- |
| `target.py` | Functions under test (provided, not modified) |
| `tests/test_target.py` | Functional tests for all 16 functions |
| `tests/test_app.py` | Tests for the web frontend and `/health` |
| `app.py`, `templates/index.html` | Flask frontend that runs every function and shows the result or error |
| `scripts/smoke_test.py` | Live smoke test used by the pipeline |
| `.github/workflows/ci.yml` | `test` → `deploy` → `smoke-test` pipeline |
| `pyproject.toml` | pytest, coverage and ruff settings |
| `requirements.txt` | Pinned dependencies |

## Setup

```bash
git clone https://github.com/atiqul96/functional-testing-2507211.git
cd functional-testing-2507211
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running the tests

```bash
pytest --cov=target --cov-branch --cov-report=term-missing --cov-fail-under=100
```

Lint:

```bash
ruff check .
ruff format --check .
```

Result: 373 tests, 100% line and branch coverage of `target.py`, no skips or xfails.

### What the tests cover

For each of the 16 functions the tests check **valid inputs**, **boundary values**,
**invalid values** and **wrong types**, using `@pytest.mark.parametrize` throughout.

- Exceptions are checked with `pytest.raises` and the exact class (`ValueError`,
  `TypeError`, `KeyError`, `ZeroDivisionError`, `OverflowError`, `AttributeError`),
  with `match=` anchored to the full message wherever `target.py` sets one.
- Result types are checked where they matter (`is True`/`is False` for booleans,
  `type(x) is float` for `divide`/`average`/`celsius_to_fahrenheit`, `type(x) is int`
  for `count_vowels`/`factorial`/`to_int`, `tuple` for `swap`, `set` for `common_items`).
- `pytest.approx` is used only for inexact floating-point results (e.g. `1/3`, `sqrt(2)`).
- Boundaries: `17/18` for `is_adult`, `0` and `-1` for `factorial`, `0`/`1` for
  `is_leap_year`, centuries vs. multiples of 400, empty list/tuple/set/dict, `0`, `0.0`,
  `-0.0` and `False` as divisors, 1- and 3-element tuples for `swap`, and so on.
- Inputs are checked not to be modified (`find_max`, `average`, `swap`, `common_items`).

The suite was also run against 47 deliberately faulty versions of `target.py`
(off-by-one boundaries, `//` instead of `/`, `|` instead of `&`, wrong leap-year rules,
missing `.lower()`, missing `strip()`, wrong error class or message, etc.).
All 47 were caught.

## Web frontend

`app.py` is a small Flask app. Each of the 16 functions has a card where you type the
arguments as Python literals (`42`, `3.5`, `"text"`, `None`, `[1, 2]`, `(1, 2)`,
`{1, 2}`, `{"apple": 1.25}`); the page shows the call, the result and its type, or the
exception class and message exactly as `target.py` raises it. Inputs are parsed with
`ast.literal_eval` (never `eval`), and very large `factorial`/`power` inputs are refused
so the public server stays responsive.

| Route | Purpose |
| --- | --- |
| `GET /` | The interactive page; the footer shows the deployed commit SHA |
| `POST /api/run` | `{"function": "divide", "args": ["10", "4"]}` → result or error |
| `GET /api/functions` | List of functions and parameters |
| `GET /health` | `{"status": "ok", "sha": "<deployed commit SHA>"}` |

Run it locally:

```bash
flask --app app run            # http://127.0.0.1:5000
```

## CI/CD pipeline

`.github/workflows/ci.yml` has three jobs and one gate:

1. **`test`** — runs on every push and on pull requests to `main`. Matrix of Python 3.10,
   3.11 and 3.12 with pip caching. Runs `ruff`, then `pytest` with
   `--cov-fail-under=100` for `target.py`, and uploads the coverage report
   (`coverage.xml` + `htmlcov/`) as an artifact for each Python version.
2. **`deploy`** — `needs: test`, and runs only for pushes to `main`. It calls the Render
   deploy hook stored in the `RENDER_DEPLOY_HOOK` secret with `&ref=<commit SHA>`, so
   Render builds exactly the commit that passed. Render's own auto-deploy is **off**.
3. **`smoke-test`** — `needs: deploy`. Polls `LIVE_URL/health` until it reports the new
   commit SHA, then checks three live requests: the page loads, `divide(10, 4)` returns
   `2.5`, and `divide(1, 0)` reports `ZeroDivisionError`.

If any test fails, `deploy` and `smoke-test` are skipped and the live site keeps
running the previous commit.

Repository settings used: secret `RENDER_DEPLOY_HOOK`, variable `LIVE_URL`, and branch
protection on `main` requiring the `test (3.10)`, `test (3.11)` and `test (3.12)` checks.

## Suspected bugs in `target.py`

`target.py` was not modified. The tests document its current behaviour; these are the
places where that behaviour looks wrong or inconsistent with its comments:

1. **`greet` has no type check.** `greet(5)` raises `AttributeError: 'int' object has no
   attribute 'strip'` instead of a clear `TypeError` like `count_vowels` and `invert` give.
2. **`power(0, -1)` is not handled.** Python's own `ZeroDivisionError` ("0.0 cannot be
   raised to a negative power") leaks out, unlike `divide`, which raises a clear message.
   `power(-8, 1/3)` silently returns a complex number, and `power(10.0, 400)` raises
   `OverflowError`.
3. **`to_int` truncates instead of rounding,** so `to_int(3.9)` is `3` and `to_int(-3.9)`
   is `-3`. It accepts the float `3.5` but rejects the string `"3.5"` with `ValueError`.
   `to_int(float("inf"))` raises `OverflowError`.
4. **Booleans are rejected in some places but accepted in others.** `to_int(True)` and
   `invert(1)` raise `TypeError`, but `is_adult(True)` returns `False`,
   `factorial(True)` returns `1`, `is_leap_year(True)` returns `False`,
   `average([True, False])` returns `0.5`, and `divide(1, False)` says "cannot divide by
   zero".
5. **`factorial` gives an unclear error for floats.** `factorial(3.0)` and
   `factorial(2.5)` raise a generic `TypeError` from `range()`
   ("'float' object cannot be interpreted as an integer") instead of a clear message.
6. **`celsius_to_fahrenheit` accepts temperatures below absolute zero** (e.g. `-300`)
   and booleans (`True` → `33.8`), with no validation.
7. **`common_items` has no type check.** Passing lists gives Python's generic
   `TypeError: unsupported operand type(s) for &`.
8. **`find_max` and `average` do not check the items are numbers.** `find_max("abc")`
   returns `'c'`, and `find_max([1, "a"])` raises a generic `TypeError`.
9. **`count_vowels` ignores accented vowels** (`"àéîõü"` → `0`), which may or may not
   be intended.
10. **`is_adult` and `is_leap_year` raise unclear errors for wrong types** (e.g.
    `is_adult("18")` raises `TypeError: '<' not supported between 'str' and 'int'`).

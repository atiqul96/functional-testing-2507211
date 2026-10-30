"""app.py - Flask web frontend that runs the functions in target.py.

Routes
  GET  /           the interactive page
  POST /api/run    run one function: {"function": "divide", "args": ["10", "4"]}
  GET  /api/functions  list of functions and their parameters
  GET  /health     {"status": "ok", "sha": "<deployed commit SHA>"}

Arguments are typed as Python literals (e.g. 42, 3.5, "text", None, True,
[1, 2], (1, 2), {1, 2}, {"apple": 1.25}) and parsed safely with ast.literal_eval.
"""

import ast
import os

from flask import Flask, jsonify, render_template, request

import target

app = Flask(__name__)

# Render sets RENDER_GIT_COMMIT automatically; GIT_SHA lets any other host set it.
DEPLOYED_SHA = os.environ.get("RENDER_GIT_COMMIT") or os.environ.get("GIT_SHA") or "dev"

MAX_INPUT_LENGTH = 1000  # characters per argument
MAX_FACTORIAL_N = 2000  # keep the public server responsive
MAX_EXPONENT = 10_000

# name -> (category, description, [(param, example), ...])
FUNCTIONS = {
    "is_adult": ("Integer", "True if age is 18 or more", [("age", "18")]),
    "celsius_to_fahrenheit": ("Float", "Celsius to Fahrenheit, 2 decimals", [("celsius", "36.6")]),
    "count_vowels": ("String", "Count a, e, i, o, u (any case)", [("text", '"Hello World"')]),
    "invert": ("Boolean", "Opposite of a bool", [("flag", "True")]),
    "greet": ("None", "Greet by name, or Guest", [("name", "None")]),
    "find_max": ("List", "Largest number in a list", [("numbers", "[3, 9, 2]")]),
    "get_price": (
        "Dictionary",
        "Price of an item",
        [("prices", '{"apple": 1.25, "bread": 3}'), ("item", '"apple"')],
    ),
    "swap": ("Tuple", "Swap the two values", [("pair", "(1, 2)")]),
    "common_items": (
        "Set",
        "Items found in both sets",
        [("set_a", "{1, 2, 3}"), ("set_b", "{2, 3, 4}")],
    ),
    "is_leap_year": ("Date", "True if year is a leap year", [("year", "2024")]),
    "to_int": ("Type conversion", "Convert a value to int", [("value", '"42"')]),
    "divide": ("Math", "a / b", [("a", "10"), ("b", "4")]),
    "power": ("Math", "base ** exponent", [("base", "2"), ("exponent", "10")]),
    "square_root": ("Math", "Square root of x", [("x", "16")]),
    "factorial": ("Math", "n!", [("n", "5")]),
    "average": ("Math", "Average of a list", [("numbers", "[1, 2, 3, 4]")]),
}


class InputError(Exception):
    """The request itself is malformed (not an error raised by target.py)."""


def parse_argument(raw):
    if not isinstance(raw, str):
        raise InputError("each argument must be sent as a string")
    if len(raw) > MAX_INPUT_LENGTH:
        raise InputError(f"argument longer than {MAX_INPUT_LENGTH} characters")
    if raw.strip() == "":
        raise InputError('argument is empty - type None for no value, or "" for an empty string')
    try:
        return ast.literal_eval(raw.strip())
    except (ValueError, SyntaxError, TypeError, MemoryError, RecursionError):
        raise InputError(
            f'could not read {raw!r} as a Python value - wrap text in quotes, e.g. "hello"'
        ) from None


def check_limits(name, args):
    """Refuse inputs that would take the public server too long to compute."""
    if name == "factorial" and isinstance(args[0], int) and args[0] > MAX_FACTORIAL_N:
        raise InputError(f"the web demo limits factorial to n <= {MAX_FACTORIAL_N}")
    if name == "power" and isinstance(args[1], (int, float)) and abs(args[1]) > MAX_EXPONENT:
        raise InputError(f"the web demo limits the exponent to +/-{MAX_EXPONENT}")


def describe(value):
    try:
        text = repr(value)
    except ValueError:  # Python refuses to print ints with more than 4300 digits
        digits = int(value.bit_length() * 0.30103) + 1
        return f"<integer with about {digits} digits>"
    return text


@app.get("/")
def index():
    return render_template("index.html", functions=FUNCTIONS, sha=DEPLOYED_SHA)


@app.get("/health")
def health():
    return jsonify(status="ok", sha=DEPLOYED_SHA)


@app.get("/api/functions")
def list_functions():
    return jsonify(
        {
            name: {"category": cat, "description": desc, "params": [p for p, _ in params]}
            for name, (cat, desc, params) in FUNCTIONS.items()
        }
    )


@app.post("/api/run")
def run():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(ok=False, error="BadRequest", message="send JSON: {function, args}"), 400

    name = payload.get("function")
    if name not in FUNCTIONS:
        return jsonify(ok=False, error="BadRequest", message=f"unknown function {name!r}"), 400

    raw_args = payload.get("args", [])
    params = FUNCTIONS[name][2]
    if not isinstance(raw_args, list) or len(raw_args) > len(params):
        return jsonify(
            ok=False, error="BadRequest", message=f"{name} takes {len(params)} argument(s)"
        ), 400

    try:
        args = [parse_argument(raw) for raw in raw_args]
        if len(args) == len(params):
            check_limits(name, args)
    except InputError as exc:
        return jsonify(ok=False, error="InputError", message=str(exc)), 400

    call = f"{name}({', '.join(repr(a) for a in args)})"
    try:
        result = getattr(target, name)(*args)
    except Exception as exc:  # show any error target.py raises, exactly as raised
        message = exc.args[0] if isinstance(exc, KeyError) and exc.args else str(exc)
        return jsonify(ok=False, call=call, error=type(exc).__name__, message=str(message))

    return jsonify(ok=True, call=call, result=describe(result), type=type(result).__name__)


if __name__ == "__main__":  # pragma: no cover
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=True)

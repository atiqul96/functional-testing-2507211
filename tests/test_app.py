"""Tests for the Flask frontend (app.py)."""

import pytest

import app as webapp


@pytest.fixture()
def client():
    webapp.app.config.update(TESTING=True)
    return webapp.app.test_client()


def run(client, function, *args):
    return client.post("/api/run", json={"function": function, "args": list(args)})


def test_index_lists_all_16_functions(client):
    res = client.get("/")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    for name in webapp.FUNCTIONS:
        assert f'data-fn="{name}"' in html
    assert len(webapp.FUNCTIONS) == 16
    assert 'id="footer-sha"' in html


def test_health_returns_sha(client, monkeypatch):
    monkeypatch.setattr(webapp, "DEPLOYED_SHA", "abc1234def")
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok", "sha": "abc1234def"}


def test_functions_endpoint(client):
    data = client.get("/api/functions").get_json()
    assert data["get_price"]["params"] == ["prices", "item"]
    assert data["divide"]["category"] == "Math"


def test_every_example_runs(client):
    for name, (_, _, params) in webapp.FUNCTIONS.items():
        data = run(client, name, *[example for _, example in params]).get_json()
        assert data["ok"] is True, (name, data)


@pytest.mark.parametrize(
    "function, args, result, type_name",
    [
        ("divide", ["10", "4"], "2.5", "float"),
        ("is_adult", ["18"], "True", "bool"),
        ("count_vowels", ['"Hello"'], "2", "int"),
        ("greet", ["None"], "'Hello, Guest!'", "str"),
        ("greet", [], "'Hello, Guest!'", "str"),
        ("swap", ["(1, 2)"], "(2, 1)", "tuple"),
        ("common_items", ["{1, 2}", "{2, 3}"], "{2}", "set"),
        ("get_price", ['{"apple": 1.25}', '"apple"'], "1.25", "float"),
        ("factorial", ["5"], "120", "int"),
    ],
)
def test_successful_calls(client, function, args, result, type_name):
    data = run(client, function, *args).get_json()
    assert data == {
        "ok": True,
        "call": data["call"],
        "result": result,
        "type": type_name,
    }
    assert data["call"].startswith(function + "(")


@pytest.mark.parametrize(
    "function, args, error, message",
    [
        ("divide", ["1", "0"], "ZeroDivisionError", "cannot divide by zero"),
        ("find_max", ["[]"], "ValueError", "list is empty"),
        ("count_vowels", ["5"], "TypeError", "text must be a string"),
        ("get_price", ["{}", '"tea"'], "KeyError", "tea not found"),
        ("to_int", ["True"], "TypeError", "bool is not allowed"),
    ],
)
def test_errors_from_target_are_shown(client, function, args, error, message):
    res = run(client, function, *args)
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is False
    assert data["error"] == error
    assert data["message"] == message


def test_missing_argument_shows_type_error(client):
    data = run(client, "divide", "1").get_json()
    assert data["ok"] is False and data["error"] == "TypeError"


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {"function": "nope", "args": []},
        {"function": "divide", "args": ["1", "2", "3"]},
        {"function": "divide", "args": "1,2"},
        {"function": "divide", "args": [1, 2]},
        {"function": "divide", "args": ["hello", "2"]},
        {"function": "divide", "args": ["", "2"]},
        {"function": "divide", "args": ["1" * 2000, "2"]},
        {"function": "divide", "args": ["__import__('os')", "2"]},
        {"function": "factorial", "args": ["100000"]},
        {"function": "power", "args": ["2", "100000"]},
    ],
)
def test_bad_requests_are_rejected(client, payload):
    res = client.post("/api/run", json=payload)
    assert res.status_code == 400
    assert res.get_json()["ok"] is False


def test_very_large_integer_result_is_summarised(client):
    data = run(client, "factorial", "2000").get_json()
    assert data["ok"] is True
    assert data["result"].startswith("<integer with about")

"""Functional tests for target.py.

Every function is tested for:
  * valid inputs (typical values),
  * boundary values (the exact edge where behaviour changes),
  * invalid values (the documented exception, with its exact class and message),
  * wrong types (what happens when the caller passes the wrong kind of value),
and, where the type of the result matters, the result type is checked too.
"""

import math

import pytest

import target


# ---------------------------------------------------------------------------
# 1. is_adult (integer)
# ---------------------------------------------------------------------------
class TestIsAdult:
    @pytest.mark.parametrize(
        "age, expected",
        [
            (0, False),  # lowest valid age
            (1, False),
            (10, False),
            (17, False),  # boundary: one below
            (18, True),  # boundary: exactly 18
            (19, True),  # boundary: one above
            (65, True),
            (150, True),
            (10**9, True),  # very large integer
        ],
    )
    def test_valid_ages(self, age, expected):
        result = target.is_adult(age)
        assert result is expected  # also proves the result is a real bool

    @pytest.mark.parametrize("age, expected", [(17.99, False), (18.0, True), (18.01, True)])
    def test_float_ages_around_boundary(self, age, expected):
        assert target.is_adult(age) is expected

    @pytest.mark.parametrize("age", [-1, -18, -1000, -0.5])
    def test_negative_age_raises(self, age):
        with pytest.raises(ValueError, match=r"^age cannot be negative$"):
            target.is_adult(age)

    @pytest.mark.parametrize("age", ["18", None, [18], {"age": 18}])
    def test_wrong_type_raises_type_error(self, age):
        with pytest.raises(TypeError):
            target.is_adult(age)


# ---------------------------------------------------------------------------
# 2. celsius_to_fahrenheit (float)
# ---------------------------------------------------------------------------
class TestCelsiusToFahrenheit:
    @pytest.mark.parametrize(
        "celsius, expected",
        [
            (0, 32.0),  # freezing point
            (100, 212.0),  # boiling point
            (-40, -40.0),  # the point where both scales meet
            (37, 98.6),  # body temperature
            (36.6, 97.88),
            (-273.15, -459.67),  # absolute zero
            (25.5, 77.9),
            (1, 33.8),
            (-17.78, -0.0),  # rounds to (negative) zero
        ],
    )
    def test_known_conversions(self, celsius, expected):
        result = target.celsius_to_fahrenheit(celsius)
        assert result == expected
        assert isinstance(result, float)

    def test_result_is_rounded_to_two_decimals(self):
        # 0.123 C -> 32.2214 F, must be rounded to 32.22
        assert target.celsius_to_fahrenheit(0.123) == 32.22
        # 0.001 C -> 32.0018 F, must be rounded to 32.0
        assert target.celsius_to_fahrenheit(0.001) == 32.0

    def test_result_never_has_more_than_two_decimals(self):
        for c in [0.1, 0.2, 0.3, 1.11, 2.345, -3.333, 99.999]:
            result = target.celsius_to_fahrenheit(c)
            assert result == round(result, 2)

    def test_integer_input_still_returns_float(self):
        assert type(target.celsius_to_fahrenheit(10)) is float

    def test_large_value(self):
        assert target.celsius_to_fahrenheit(1_000_000) == 1_800_032.0

    @pytest.mark.parametrize("bad", ["0", None, [0], {0: 0}])
    def test_wrong_type_raises_type_error(self, bad):
        with pytest.raises(TypeError):
            target.celsius_to_fahrenheit(bad)


# ---------------------------------------------------------------------------
# 3. count_vowels (string)
# ---------------------------------------------------------------------------
class TestCountVowels:
    @pytest.mark.parametrize(
        "text, expected",
        [
            ("", 0),  # empty string
            ("a", 1),  # single vowel
            ("b", 0),  # single consonant
            ("hello", 2),
            ("HELLO", 2),  # upper case counts too
            ("HeLLo WoRLD", 3),  # mixed case
            ("aeiou", 5),
            ("AEIOU", 5),
            ("aAeEiIoOuU", 10),
            ("rhythm", 0),  # 'y' is not a vowel here
            ("yY", 0),
            ("bcdfg", 0),
            ("12345 !?", 0),  # digits and punctuation
            ("   ", 0),  # whitespace only
            ("a e i o u", 5),
            ("banana", 3),
            ("Programming in Python", 5),
            ("\taei\n", 3),
            ("aaaaaaaaaa", 10),
        ],
    )
    def test_counts(self, text, expected):
        result = target.count_vowels(text)
        assert result == expected
        assert type(result) is int

    def test_accented_vowels_are_not_counted(self):
        # Only plain a, e, i, o, u are vowels for this function.
        assert target.count_vowels("àéîõü") == 0

    def test_long_string(self):
        assert target.count_vowels("ab" * 10_000) == 10_000

    @pytest.mark.parametrize("bad", [None, 123, 1.5, ["a", "e"], ("a",), {"a"}, b"aeiou", True])
    def test_non_string_raises(self, bad):
        with pytest.raises(TypeError, match=r"^text must be a string$"):
            target.count_vowels(bad)


# ---------------------------------------------------------------------------
# 4. invert (boolean)
# ---------------------------------------------------------------------------
class TestInvert:
    @pytest.mark.parametrize("flag, expected", [(True, False), (False, True)])
    def test_inverts(self, flag, expected):
        assert target.invert(flag) is expected

    @pytest.mark.parametrize("flag", [True, False])
    def test_double_invert_returns_original(self, flag):
        assert target.invert(target.invert(flag)) is flag

    @pytest.mark.parametrize("bad", [0, 1, -1, 0.0, 1.0, "True", "False", "", None, [], [True]])
    def test_non_bool_raises(self, bad):
        with pytest.raises(TypeError, match=r"^flag must be True or False$"):
            target.invert(bad)


# ---------------------------------------------------------------------------
# 5. greet (None)
# ---------------------------------------------------------------------------
class TestGreet:
    @pytest.mark.parametrize(
        "name, expected",
        [
            ("Alice", "Hello, Alice!"),
            ("Bob", "Hello, Bob!"),
            ("A", "Hello, A!"),  # single character
            ("  Bob  ", "Hello, Bob!"),  # surrounding spaces stripped
            ("\tBob\n", "Hello, Bob!"),  # tabs/newlines stripped
            ("Mary Ann", "Hello, Mary Ann!"),  # inner space kept
            ("Guest", "Hello, Guest!"),
            ("0", "Hello, 0!"),
            ("José", "Hello, José!"),
        ],
    )
    def test_greets_by_name(self, name, expected):
        assert target.greet(name) == expected

    def test_no_argument_greets_guest(self):
        assert target.greet() == "Hello, Guest!"

    @pytest.mark.parametrize("name", [None, "", " ", "     ", "\t", "\n", " \t\n "])
    def test_none_empty_or_blank_greets_guest(self, name):
        assert target.greet(name) == "Hello, Guest!"

    def test_returns_string(self):
        assert type(target.greet("Alice")) is str
        assert type(target.greet()) is str

    @pytest.mark.parametrize("bad", [5, 1.5, ["Alice"], True])
    def test_non_string_name_raises_attribute_error(self, bad):
        # Suspected bug: a non-string name gives AttributeError, not TypeError.
        with pytest.raises(AttributeError):
            target.greet(bad)


# ---------------------------------------------------------------------------
# 6. find_max (list)
# ---------------------------------------------------------------------------
class TestFindMax:
    @pytest.mark.parametrize(
        "numbers, expected",
        [
            ([5], 5),  # single element
            ([1, 2, 3], 3),  # max at the end
            ([3, 2, 1], 3),  # max at the start
            ([1, 9, 2], 9),  # max in the middle
            ([-5, -2, -9], -2),  # all negative
            ([-1, 0, 1], 1),
            ([0, 0, 0], 0),
            ([7, 7, 3], 7),  # duplicate max
            ([1.5, 2.5, 2.4], 2.5),  # floats
            ([1, 2.5, 2], 2.5),  # mixed int/float
            ([10**18, 10**18 + 1], 10**18 + 1),
            ([-math.inf, 0], 0),
            ([math.inf, 0], math.inf),
        ],
    )
    def test_returns_largest(self, numbers, expected):
        assert target.find_max(numbers) == expected

    def test_keeps_element_type(self):
        assert type(target.find_max([1, 2, 3])) is int
        assert type(target.find_max([1.0, 2.0])) is float

    def test_does_not_modify_list(self):
        numbers = [3, 1, 2]
        target.find_max(numbers)
        assert numbers == [3, 1, 2]

    def test_works_with_tuple(self):
        assert target.find_max((4, 8, 6)) == 8

    def test_empty_list_raises(self):
        with pytest.raises(ValueError, match=r"^list is empty$"):
            target.find_max([])

    def test_empty_tuple_raises(self):
        with pytest.raises(ValueError, match=r"^list is empty$"):
            target.find_max(())

    @pytest.mark.parametrize("bad", [None, 5, 3.2])
    def test_no_length_raises_type_error(self, bad):
        with pytest.raises(TypeError):
            target.find_max(bad)

    def test_mixed_uncomparable_items_raise_type_error(self):
        with pytest.raises(TypeError):
            target.find_max([1, "a"])


# ---------------------------------------------------------------------------
# 7. get_price (dictionary)
# ---------------------------------------------------------------------------
PRICES = {"apple": 1.25, "bread": 3, "free": 0, "milk": 0.99, "": 5}


class TestGetPrice:
    @pytest.mark.parametrize(
        "item, expected",
        [("apple", 1.25), ("bread", 3), ("milk", 0.99), ("free", 0), ("", 5)],
    )
    def test_existing_items(self, item, expected):
        assert target.get_price(PRICES, item) == expected

    def test_returns_exact_stored_object(self):
        price = target.get_price(PRICES, "bread")
        assert price == 3 and type(price) is int

    def test_zero_price_is_returned_not_treated_as_missing(self):
        assert target.get_price(PRICES, "free") == 0

    def test_none_value_is_returned(self):
        assert target.get_price({"x": None}, "x") is None

    def test_non_string_keys(self):
        assert target.get_price({1: "one", (1, 2): "pair"}, 1) == "one"
        assert target.get_price({1: "one", (1, 2): "pair"}, (1, 2)) == "pair"

    def test_does_not_modify_dict(self):
        prices = {"a": 1}
        target.get_price(prices, "a")
        assert prices == {"a": 1}

    @pytest.mark.parametrize("item", ["banana", "Apple", "apple ", "APPLE"])
    def test_missing_item_raises(self, item):
        # lookup is exact: case and spaces matter
        with pytest.raises(KeyError, match=rf"^'{item} not found'$"):
            target.get_price(PRICES, item)

    def test_empty_dict_raises(self):
        with pytest.raises(KeyError, match=r"apple not found"):
            target.get_price({}, "apple")

    def test_none_prices_raises_type_error(self):
        with pytest.raises(TypeError):
            target.get_price(None, "apple")


# ---------------------------------------------------------------------------
# 8. swap (tuple)
# ---------------------------------------------------------------------------
class TestSwap:
    @pytest.mark.parametrize(
        "pair, expected",
        [
            ((1, 2), (2, 1)),
            (("a", "b"), ("b", "a")),
            ((1, "x"), ("x", 1)),
            ((None, 0), (0, None)),
            ((5, 5), (5, 5)),  # identical values
            (((1, 2), [3]), ([3], (1, 2))),  # nested values
        ],
    )
    def test_swaps(self, pair, expected):
        result = target.swap(pair)
        assert result == expected
        assert type(result) is tuple

    def test_list_input_returns_tuple(self):
        result = target.swap([1, 2])
        assert result == (2, 1)
        assert type(result) is tuple

    def test_swap_twice_returns_original(self):
        assert target.swap(target.swap((1, 2))) == (1, 2)

    def test_does_not_modify_input(self):
        pair = [1, 2]
        target.swap(pair)
        assert pair == [1, 2]

    @pytest.mark.parametrize("pair", [(), (1,), (1, 2, 3), (1, 2, 3, 4), [], [1]])
    def test_wrong_length_raises(self, pair):
        with pytest.raises(ValueError, match=r"^pair must have exactly 2 values$"):
            target.swap(pair)

    @pytest.mark.parametrize("bad", [None, 12, 1.5])
    def test_no_length_raises_type_error(self, bad):
        with pytest.raises(TypeError):
            target.swap(bad)


# ---------------------------------------------------------------------------
# 9. common_items (set)
# ---------------------------------------------------------------------------
class TestCommonItems:
    @pytest.mark.parametrize(
        "set_a, set_b, expected",
        [
            ({1, 2, 3}, {2, 3, 4}, {2, 3}),  # partial overlap
            ({1, 2}, {3, 4}, set()),  # no overlap
            ({1, 2}, {1, 2}, {1, 2}),  # identical
            ({1}, {1, 2, 3}, {1}),  # subset
            (set(), {1, 2}, set()),  # one empty
            ({1, 2}, set(), set()),
            (set(), set(), set()),  # both empty
            ({"a", "b"}, {"b", "c"}, {"b"}),  # strings
            ({"A"}, {"a"}, set()),  # case-sensitive
            ({(1, 2), 3}, {(1, 2)}, {(1, 2)}),  # tuples as members
        ],
    )
    def test_intersection(self, set_a, set_b, expected):
        result = target.common_items(set_a, set_b)
        assert result == expected
        assert isinstance(result, set)

    def test_order_does_not_matter(self):
        a, b = {1, 2, 3}, {3, 4, 1}
        assert target.common_items(a, b) == target.common_items(b, a)

    def test_inputs_are_not_modified(self):
        a, b = {1, 2}, {2, 3}
        target.common_items(a, b)
        assert a == {1, 2} and b == {2, 3}

    def test_result_is_a_new_set(self):
        a = {1, 2}
        result = target.common_items(a, {1, 2})
        assert result is not a

    def test_frozensets(self):
        assert target.common_items(frozenset({1, 2}), frozenset({2})) == {2}

    @pytest.mark.parametrize(
        "set_a, set_b", [([1, 2], [2]), ({1, 2}, [2]), (None, {1}), ("ab", "b")]
    )
    def test_non_sets_raise_type_error(self, set_a, set_b):
        with pytest.raises(TypeError):
            target.common_items(set_a, set_b)


# ---------------------------------------------------------------------------
# 10. is_leap_year (date)
# ---------------------------------------------------------------------------
class TestIsLeapYear:
    @pytest.mark.parametrize(
        "year, expected",
        [
            (1, False),  # lowest allowed year
            (4, True),  # first leap year
            (100, False),  # century, not divisible by 400
            (400, True),  # divisible by 400
            (1600, True),
            (1700, False),
            (1800, False),
            (1900, False),
            (1996, True),
            (1999, False),
            (2000, True),
            (2001, False),
            (2020, True),
            (2023, False),
            (2024, True),
            (2100, False),
            (2400, True),
            (10000, True),
        ],
    )
    def test_years(self, year, expected):
        assert target.is_leap_year(year) is expected

    @pytest.mark.parametrize("year", [0, -1, -4, -400])
    def test_year_below_one_raises(self, year):
        with pytest.raises(ValueError, match=r"^year must be 1 or more$"):
            target.is_leap_year(year)

    @pytest.mark.parametrize("bad", ["2024", None, [2024]])
    def test_wrong_type_raises_type_error(self, bad):
        with pytest.raises(TypeError):
            target.is_leap_year(bad)


# ---------------------------------------------------------------------------
# 11. to_int (type conversion)
# ---------------------------------------------------------------------------
class TestToInt:
    @pytest.mark.parametrize(
        "value, expected",
        [
            (5, 5),
            (0, 0),
            (-5, -5),
            ("42", 42),
            ("-7", -7),
            ("+7", 7),
            ("0", 0),
            (" 42 ", 42),  # surrounding spaces are allowed by int()
            ("007", 7),
            ("1_000", 1000),
            (3.0, 3),
            (3.9, 3),  # truncates toward zero, does not round
            (-3.9, -3),
            (0.5, 0),
            (10**20, 10**20),
        ],
    )
    def test_converts(self, value, expected):
        result = target.to_int(value)
        assert result == expected
        assert type(result) is int

    @pytest.mark.parametrize("value", [True, False])
    def test_bool_raises(self, value):
        with pytest.raises(TypeError, match=r"^bool is not allowed$"):
            target.to_int(value)

    @pytest.mark.parametrize("value", ["", "abc", "3.5", "4x", "1 2", " "])
    def test_bad_string_raises_value_error(self, value):
        with pytest.raises(ValueError):
            target.to_int(value)

    @pytest.mark.parametrize("value", [None, [1], {1: 1}, (1,)])
    def test_bad_type_raises_type_error(self, value):
        with pytest.raises(TypeError):
            target.to_int(value)

    @pytest.mark.parametrize("value", [math.inf, -math.inf])
    def test_infinity_raises_overflow_error(self, value):
        with pytest.raises(OverflowError):
            target.to_int(value)

    def test_nan_raises_value_error(self):
        with pytest.raises(ValueError):
            target.to_int(math.nan)


# ---------------------------------------------------------------------------
# 12. divide (math)
# ---------------------------------------------------------------------------
class TestDivide:
    @pytest.mark.parametrize(
        "a, b, expected",
        [
            (10, 2, 5.0),
            (7, 2, 3.5),
            (-10, 2, -5.0),
            (10, -2, -5.0),
            (-10, -2, 5.0),
            (0, 5, 0.0),
            (5, 1, 5.0),
            (1, 4, 0.25),
            (2.5, 0.5, 5.0),
        ],
    )
    def test_exact_results(self, a, b, expected):
        result = target.divide(a, b)
        assert result == expected
        assert type(result) is float  # true division, never int

    @pytest.mark.parametrize(
        "a, b, expected",
        [(1, 3, 0.3333333333), (2, 3, 0.6666666667), (0.1, 0.3, 0.3333333333)],
    )
    def test_inexact_results(self, a, b, expected):
        assert target.divide(a, b) == pytest.approx(expected)

    def test_tiny_divisor(self):
        assert target.divide(1, 1e-10) == pytest.approx(1e10)

    @pytest.mark.parametrize("a", [0, 1, -1, 2.5])
    @pytest.mark.parametrize("b", [0, 0.0, -0.0, False])
    def test_divide_by_zero_raises(self, a, b):
        with pytest.raises(ZeroDivisionError, match=r"^cannot divide by zero$"):
            target.divide(a, b)

    @pytest.mark.parametrize("a, b", [("10", 2), (10, "2"), (None, 1), ([1], 1)])
    def test_wrong_types_raise_type_error(self, a, b):
        with pytest.raises(TypeError):
            target.divide(a, b)


# ---------------------------------------------------------------------------
# 13. power (math)
# ---------------------------------------------------------------------------
class TestPower:
    @pytest.mark.parametrize(
        "base, exponent, expected",
        [
            (2, 3, 8),
            (2, 0, 1),  # anything to the 0 is 1
            (0, 0, 1),  # Python defines 0 ** 0 as 1
            (0, 5, 0),
            (1, 1000, 1),
            (5, 1, 5),
            (-2, 3, -8),  # negative base, odd exponent
            (-2, 2, 4),  # negative base, even exponent
            (10, 6, 1_000_000),
            (2, 100, 2**100),
        ],
    )
    def test_integer_results(self, base, exponent, expected):
        result = target.power(base, exponent)
        assert result == expected
        assert type(result) is int

    @pytest.mark.parametrize(
        "base, exponent, expected",
        [(2, -1, 0.5), (2, -2, 0.25), (4, 0.5, 2.0), (2.0, 3, 8.0), (9, 0.5, 3.0)],
    )
    def test_float_results(self, base, exponent, expected):
        result = target.power(base, exponent)
        assert result == expected
        assert type(result) is float

    def test_inexact_result(self):
        assert target.power(2, 0.5) == pytest.approx(math.sqrt(2))

    def test_negative_base_fractional_exponent_gives_complex(self):
        result = target.power(-8, 1 / 3)
        assert type(result) is complex
        assert result == pytest.approx(complex(1, math.sqrt(3)))

    def test_zero_to_negative_power_raises(self):
        # Suspected bug: not handled, Python's own ZeroDivisionError leaks out.
        with pytest.raises(ZeroDivisionError):
            target.power(0, -1)

    def test_float_overflow_raises(self):
        with pytest.raises(OverflowError):
            target.power(10.0, 400)

    @pytest.mark.parametrize("base, exponent", [("2", 3), (2, "3"), (None, 2)])
    def test_wrong_types_raise_type_error(self, base, exponent):
        with pytest.raises(TypeError):
            target.power(base, exponent)


# ---------------------------------------------------------------------------
# 14. square_root (math)
# ---------------------------------------------------------------------------
class TestSquareRoot:
    @pytest.mark.parametrize(
        "x, expected",
        [(0, 0.0), (1, 1.0), (4, 2.0), (9, 3.0), (16, 4.0), (0.25, 0.5), (1e10, 1e5)],
    )
    def test_perfect_squares(self, x, expected):
        result = target.square_root(x)
        assert result == expected
        assert type(result) is float

    @pytest.mark.parametrize("x, expected", [(2, 1.41421356), (3, 1.73205081), (0.5, 0.70710678)])
    def test_inexact_roots(self, x, expected):
        assert target.square_root(x) == pytest.approx(expected)

    def test_tiny_positive(self):
        assert target.square_root(1e-10) == pytest.approx(1e-5)

    def test_negative_zero_is_allowed(self):
        assert target.square_root(-0.0) == 0.0

    def test_result_squared_gives_input(self):
        for x in [2, 7, 123.456]:
            assert target.square_root(x) ** 2 == pytest.approx(x)

    @pytest.mark.parametrize("x", [-1, -0.0001, -4, -1e10])
    def test_negative_raises(self, x):
        with pytest.raises(ValueError, match=r"^cannot take the square root of a negative number$"):
            target.square_root(x)

    @pytest.mark.parametrize("bad", ["4", None, [4]])
    def test_wrong_type_raises_type_error(self, bad):
        with pytest.raises(TypeError):
            target.square_root(bad)


# ---------------------------------------------------------------------------
# 15. factorial (math)
# ---------------------------------------------------------------------------
class TestFactorial:
    @pytest.mark.parametrize(
        "n, expected",
        [
            (0, 1),  # boundary: 0! is 1
            (1, 1),
            (2, 2),
            (3, 6),
            (4, 24),
            (5, 120),
            (10, 3_628_800),
            (20, 2_432_902_008_176_640_000),
        ],
    )
    def test_values(self, n, expected):
        result = target.factorial(n)
        assert result == expected
        assert type(result) is int

    def test_matches_math_factorial(self):
        for n in range(0, 30):
            assert target.factorial(n) == math.factorial(n)

    def test_large_value_is_exact(self):
        assert target.factorial(50) == math.factorial(50)

    @pytest.mark.parametrize("n", [-1, -2, -100])
    def test_negative_raises(self, n):
        with pytest.raises(ValueError, match=r"^factorial is not defined for negative numbers$"):
            target.factorial(n)

    @pytest.mark.parametrize("n", [2.5, 3.0])
    def test_float_raises_type_error(self, n):
        with pytest.raises(TypeError):
            target.factorial(n)

    @pytest.mark.parametrize("bad", ["5", None])
    def test_wrong_type_raises_type_error(self, bad):
        with pytest.raises(TypeError):
            target.factorial(bad)


# ---------------------------------------------------------------------------
# 16. average (math)
# ---------------------------------------------------------------------------
class TestAverage:
    @pytest.mark.parametrize(
        "numbers, expected",
        [
            ([5], 5.0),  # single element
            ([1, 2, 3], 2.0),
            ([1, 2], 1.5),
            ([0, 0, 0], 0.0),
            ([-1, 1], 0.0),
            ([-2, -4], -3.0),
            ([2.5, 3.5], 3.0),
            ([10, 20, 30, 40], 25.0),
            ([10**6, 10**6], 1_000_000.0),
        ],
    )
    def test_exact_averages(self, numbers, expected):
        result = target.average(numbers)
        assert result == expected
        assert type(result) is float

    @pytest.mark.parametrize("numbers, expected", [([1, 2, 2], 1.6666666667), ([0.1, 0.2], 0.15)])
    def test_inexact_averages(self, numbers, expected):
        assert target.average(numbers) == pytest.approx(expected)

    def test_works_with_tuple(self):
        assert target.average((2, 4)) == 3.0

    def test_does_not_modify_list(self):
        numbers = [1, 2, 3]
        target.average(numbers)
        assert numbers == [1, 2, 3]

    @pytest.mark.parametrize("empty", [[], ()])
    def test_empty_raises(self, empty):
        with pytest.raises(ValueError, match=r"^list is empty$"):
            target.average(empty)

    @pytest.mark.parametrize("bad", [None, 5, ["1", "2"]])
    def test_wrong_type_raises_type_error(self, bad):
        with pytest.raises(TypeError):
            target.average(bad)

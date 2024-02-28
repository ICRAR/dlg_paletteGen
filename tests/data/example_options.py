"""
Tests for various options passing type information.

Expected behavior follows preference order:
1. Type hints
2. default value type guessing
3. docstring type hints in params

Rationale: docstrings are the least likely to be well maintained.
"""

import benedict
from typing import Any, Union
import numpy as np


def testField(
    test_pos_hint: str,
    test_pos_hint_doc: any,
    test_pos_doc,
    test_kw_hint: int = 1,
    test_kw_hint_doc: float = 5.0,
    test_kw_doc=True,
    test_kw_guess=[1, 2, 3],
    test_kw_json: list = [3, 4, 5],
    test_kw_non_json: dict = {"a": "hello"},
    test_kw_complex1: np.array = np.array([123, 456]),
    test_kw_complex2: benedict.benedict = benedict.benedict(),
    test_kw_none: Union[str, None] = None,
) -> dict:
    """
    Construct a dummy field

    :param test_pos_hint: type hint only (positional)
    :param test_pos_hint_doc: str, type hint and wrong docstring (positional)
    :param test_pos_doc: float, docstring only (positional)
    :param test_kw_hint: type hint only (kw)
    :param test_kw_hint_doc: float, type hint and docstring (kw)
    :param test_kw_doc: list, docstring only (kw)
    :param test_kw_guess: default value guessing (kw)
    :param test_kw_json: complex standard type supported by JSON in type hint
    :param test_kw_non_json: complex standard type NOT supported by JSON in type hint
    :param test_kw_complex1: complex non-standard type (numpy array)
    :param test_kw_complex2: complex non-standard type (benedict dictionary)
    :param test_none: none type in default_value
    """
    test_field = benedict.benedict()
    fieldValue = benedict.benedict()
    fieldValue.pos_hint = test_pos_hint
    fieldValue.pos_hint_doc = test_pos_hint_doc
    fieldValue.pos_doc = test_pos_doc
    fieldValue.kw_hint = test_kw_hint
    fieldValue.kw_hint_doc = test_kw_hint_doc
    fieldValue.kw_doc = test_kw_doc
    fieldValue.guess = test_kw_guess
    fieldValue.json = test_kw_json
    fieldValue.non_json = test_kw_non_json
    fieldValue.complex1 = test_kw_complex1
    fieldValue.complex2 = test_kw_complex2
    fieldValue.none = test_kw_none
    test_field.__setattr__(test_pos_hint, fieldValue)
    return test_field


def testFieldSingle(
    test_pos_hint: str,
    test_pos_hint_doc: any,
    test_pos_doc,
    test_kw_hint: int = 1,
    test_kw_hint_doc: float = 5.0,
    test_kw_doc=True,
    test_kw_guess=[1, 2, 3],
    test_kw_json: list = [3, 4, 5],
    test_kw_non_json: dict = {"a": "hello"},
    test_kw_complex1: np.array = np.array([123, 456]),
    test_kw_complex2: benedict.benedict = benedict.benedict(),
    test_kw_none: Union[str, None] = None,
) -> dict:
    """
    Construct a dummy field

    :param test_pos_hint: type hint only (positional)
    :param test_pos_hint_doc: str, type hint and wrong docstring (positional)
    :param test_pos_doc: float, docstring only (positional)
    :param test_kw_hint: type hint only (kw)
    :param test_kw_hint_doc: float, type hint and docstring (kw)
    :param test_kw_doc: list, docstring only (kw)
    :param test_kw_guess: default value guessing (kw)
    :param test_kw_json: complex standard type supported by JSON in type hint
    :param test_kw_non_json: complex standard type NOT supported by JSON in type hint
    :param test_kw_complex1: complex non-standard type (numpy array)
    :param test_kw_complex2: complex non-standard type (benedict dictionary)
    :param test_none: none type in default_value
    """
    test_field = benedict.benedict()
    fieldValue = benedict.benedict()
    fieldValue.pos_hint = test_pos_hint
    fieldValue.pos_hint_doc = test_pos_hint_doc
    fieldValue.pos_doc = test_pos_doc
    fieldValue.kw_hint = test_kw_hint
    fieldValue.kw_hint_doc = test_kw_hint_doc
    fieldValue.kw_doc = test_kw_doc
    fieldValue.guess = test_kw_guess
    fieldValue.json = test_kw_json
    fieldValue.non_json = test_kw_non_json
    fieldValue.complex1 = test_kw_complex1
    fieldValue.complex2 = test_kw_complex2
    fieldValue.none = test_kw_none
    test_field.__setattr__(test_pos_hint, fieldValue)
    return test_field

import os
import sys

import pytest

sys.path.append(os.path.abspath(".."))
import DRMgr
import pcbnew


def test_nested_dicts_1():
    dict1 = {
        "board": {"rules": {1: 2, 3: 4, "next": {11: 12}}, "plot": {5: 6, 7: 8}},
        "positions": {9: 10},
    }
    dict2 = {}
    DRMgr.copy_nested_dict(dict1, dict2, "board|rules|next")
    print(dict2)


def test_nested_dicts_2():
    dict1 = {
        "board": {"rules": {1: 2, 3: 4, "next": {11: 12}}, "plot": {5: 6, 7: 8}},
        "positions": {9: 10},
    }
    dict2 = {}
    DRMgr.copy_nested_dict(dict1, dict2, "board|rules|next|null")
    print(dict2)


def test_nested_dicts_3():
    dict1 = {
        "board": {"rules": {1: 2, 3: 4, "next": {11: 12}}, "plot": {5: 6, 7: 8}},
        "positions": {9: 10},
    }
    dict2 = {}
    DRMgr.copy_nested_dict(dict1, dict2, "board|rules")
    print(dict2)

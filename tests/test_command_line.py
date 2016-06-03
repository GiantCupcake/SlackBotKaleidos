from command_line import *

#def test_state_validate_words():
#    assert ["b","a"] == state_validate_words(["b"], ["a"])
#    assert ["b","c","e"] == state_validate_words(["b","c"],["c"],["e"])

values = {"a": 1,"ab": 4,"ac": 4,"ae": 1}
words = [["a","ab","ae"],["a","ae","ac"]]

def test_clean_words():
    assert [["ab","ac"],["ad"]] == clean_words([["a","ab","ac"],["a","ad","ae"]],["a","ae"])


def test_points_per_words():
    b = points_per_words(words)
    assert values.keys() == b.keys()
    assert b["a"] == 1
    assert b["ab"] == 4

def test_count_points():
    print(count_points(words,values))
    assert [6,6] == count_points(words,values)
    assert [0,1] == count_points([[],["a"]],values)

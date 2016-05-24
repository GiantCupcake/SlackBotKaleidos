from command_line import state_validate_words

def test_state_validate_words():
    assert [["a"], ["b"]] == state_validate_words(["b"], ["a"])

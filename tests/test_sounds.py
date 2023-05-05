from sounds import notation_to_frequency


def test_note_to_freq():
    f = notation_to_frequency("A0")
    assert f == 27.5

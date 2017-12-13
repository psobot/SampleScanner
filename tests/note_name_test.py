from lib.utils import note_name, note_number


def test_note_name():
    assert 'C3' == note_name(60)
    assert 'Db3' == note_name(61)
    assert 'D3' == note_name(62)
    assert 'Eb3' == note_name(63)
    assert 'E3' == note_name(64)
    assert 'F3' == note_name(65)
    assert 'Gb3' == note_name(66)
    assert 'G3' == note_name(67)
    assert 'Ab3' == note_name(68)
    assert 'A4' == note_name(69)
    assert 'Bb4' == note_name(70)
    assert 'B4' == note_name(71)


def test_note_number():
    assert 60 == note_number('C3')
    assert 60 == note_number('c3')
    assert 61 == note_number('Db3')
    assert 61 == note_number('db3')

from lib.utils import sample_value_to_db, percent_to_db


def test_sample_value_to_db():
    assert str(sample_value_to_db(0)) == "-inf"
    assert sample_value_to_db(1) == -90.30899869919435


def test_percent_to_db():
    assert percent_to_db(0.000030518) == -90.30887862628592
    assert str(percent_to_db(0)) == "-inf"

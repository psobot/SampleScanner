from lib.utils import sample_value_to_db, percent_to_db, dbfs_as_percent


def test_sample_value_to_db():
    assert str(sample_value_to_db(0)) == "-inf"
    assert sample_value_to_db(1) == -90.30899869919435


def test_percent_to_db():
    assert percent_to_db(0.000030518) == -90.30887862628592
    assert str(percent_to_db(0)) == "-inf"


def test_dbfs_as_percent():
    minimum_16_bit_dbfs = -90.30899869919435
    assert dbfs_as_percent(minimum_16_bit_dbfs) == 0
    assert dbfs_as_percent(0) == 1

from kiss_cf.buffer import Buffer


def test_init():
    buffer = Buffer()
    # Expected default storage dir to remain consistent with other modules:
    assert buffer.storageDir == './data/buffer'

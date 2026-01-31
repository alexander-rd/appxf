from appxf_private.buffer import Buffer, buffered
from appxf_private.storage import Storage

# Used to test logging:
# from appxf import logging as kiss_logging
# kiss_logging.activate_logging()


def assert_buffer_contains(buffer: Buffer,
                           what: str,
                           inputlist: list, exact=True):
    '''Check if buffer contains "the one" what with exactly the inputs'''
    # check "what"
    whatlist = buffer.buffer.keys()
    assert what in whatlist
    assert len(whatlist) == 1
    # check "input"
    for input in buffer.buffer[what].keys():
        assert buffer.isbuffered(what, input)
    assert len(buffer.buffer[what].keys()) == len(inputlist)


# 1) Tests for class Buffer
def test_init():
    Storage.reset()
    buffer = Buffer()
    # Expected default storage dir to remain consistent with other modules:
    assert not buffer.buffer


# 2) Tests for decorator @buffered

# TODO: There is not really a check if the functions to be buffered were
# executed (agagin) >> check missing.

def test_buffered_args():
    Storage.reset()
    buffer = Buffer()

    @buffered(buffer)
    def test_func(argOne, argTwo):
        return argOne+argTwo

    assert test_func(1, 20) == 21
    assert buffer.isbuffered('test_func', '1,20')
    assert_buffer_contains(buffer, 'test_func', ['1,20'])
    assert test_func(12, 0) == 12
    assert_buffer_contains(buffer, 'test_func', ['1,20', '12,0'])


def test_buffered_kwargs():
    Storage.reset()
    buffer = Buffer()

    @buffered(buffer)
    def test_func(a=1, b=2, c=3):
        # adding a local variable since implementation might use inspection of
        # code object
        tmp = b*(c+1)
        return a + tmp

    assert test_func() == 9
    # The empty call must be stored with default values
    assert_buffer_contains(buffer, 'test_func', ['1,2,3'])
    assert test_func(a=1, b=2, c=3) == 9
    assert test_func(c=3, b=2, a=1) == 9
    assert_buffer_contains(buffer, 'test_func', ['1,2,3'])


def test_buffered_mixedargs():
    Storage.reset()
    buffer = Buffer()

    @buffered(buffer)
    def test_func(a, b, c='hello', d=15):
        # adding a local variable since implementation might use inspection of
        # code object
        tmp = b+d
        return f'{a}, {c}: {tmp}'

    assert test_func('bah', 42) == 'bah, hello: 57'
    assert_buffer_contains(buffer, 'test_func', ['bah,42,hello,15'])
    assert test_func('bah', 42, c='hello', d=15) == 'bah, hello: 57'
    assert_buffer_contains(buffer, 'test_func', ['bah,42,hello,15'])

    assert test_func('this', 3, 'that', 4) == 'this, that: 7'
    assert_buffer_contains(buffer, 'test_func', ['bah,42,hello,15',
                                                 'this,3,that,4'])


# Used to test logging:
if __name__ == '__main__':
    test_init()
    test_buffered_args()
    test_buffered_kwargs()
    test_buffered_mixedargs()
    print('tests done')

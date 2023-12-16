import pytest

from kiss_cf.utility.chain import Chain, Step

class IncrementingStep(Step):
    def __init__(self):
        super().__init__()

    def process_forward(self, data):
        return data+1

    def process_backward(self, data):
        return data-1

class DoublingStep(Step):
    def __init__(self):
        super().__init__()

    def process_forward(self, data):
        return data*2

    def process_backward(self, data):
        return data/2


def test_chain():
    chain = Chain([IncrementingStep()]*5)
    assert chain.process_forward(5) == 10
    assert chain.process_backward(5) == 0

def test_alternating_chain():
    chain = Chain([DoublingStep(), IncrementingStep(), DoublingStep()])
    assert chain.process_forward(5) == (5*2+1)*2
    assert chain.process_backward(14) == (14/2-1)/2
    # test reversed chain
    reversed_chain = chain.get_reversed_chain()
    assert reversed_chain.process_forward(14) == (14/2-1)/2
    assert reversed_chain.process_backward(5) == (5*2+1)*2
    # a few fancy back and forth computations
    assert 42 == chain.process_forward(chain.process_backward(42))
    assert 42 == chain.process_backward(chain.process_forward(42))
    assert 42 == chain.process_forward(reversed_chain.process_forward(42))
    assert 42 == chain.process_backward(reversed_chain.process_backward(42))
    assert 42 == reversed_chain.process_forward(chain.process_forward(42))
    assert 42 == reversed_chain.process_backward(chain.process_backward(42))
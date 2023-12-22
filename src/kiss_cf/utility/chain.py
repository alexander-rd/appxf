# allow class name being used as type hint in same class:
from __future__ import annotations

# from kiss_cf.storage.storage import Storable, StorageMethod


class ForwardStep(): # pragma: no cover
    '''A ForwardStep can only be processed forwards

    A step processing might consume and produce data (not returning None),
    dependent on implementation.
    '''
    def __init__(self):
        pass

    def process_forward(self, data=None):
        return data

    def __str__(self):
        return self.__class__.__name__


class Step(ForwardStep): # pragma: no cover
    '''A Step can be processed forwards and backwards

    A step processing might consume and produce data (not returning None),
    dependent on implementation. This is true for forward and backward
    processing.
    '''
    def __init__(self):
        super().__init__()

    def process_backward(self, data=None):
        return data


class ReversedStep(Step): # pragma: no cover
    def __init__(self, step: ForwardStep | Step):
        if not isinstance(step, Step):
            raise Exception(
                f'Cannot create ReversedStep ({step.__class__.__name__}) '
                f'it is likely only a ForwardStep')
        self.step = step

    def process_forward(self, data=None):
        return self.step.process_backward(data)

    def process_backward(self, data=None):
        return self.step.process_forward(data)


class Chain(): # pragma: no cover
    '''A chain of multiple steps.

    If the chain contains a single ForwardStep, it can only be processed
    forwards. Otherwise, it can also be processed backwards.
    '''
    def __init__(self, chain: list[ForwardStep | Step] = []):
        self.chain: list[ForwardStep | Step] = chain

    def __str__(self):
        return ('Chain[' +
                ', '.join([item.__class__.__name__ for item in self.chain]) +
                ']')

    def process_forward(self, data=None):
        for item in self.chain:
            data = item.process_forward(data)
        return data

    def process_backward(self, data=None):
        for item in reversed(self.chain):
            if isinstance(item, Step):
                data = item.process_backward(data)
            else:
                raise Exception(
                    f'Cannot process the chain {self} backwards. '
                    f'The item {item.__class__.__name__} is likely '
                    f'only a ForwardStep or no Step at all.')
        return data

    def append(self, step: ForwardStep | Step):
        self.chain.append(step)

    def get_reversed_chain(self) -> Chain:
        return Chain([ReversedStep(step) for step in reversed(self.chain)])

# class DataChain(Chain):
#     def __init__(self):
#         self.data = None
#
#     def get_previous_data(self):
#         class_name = self.previous.__class__.__name__
#         if not self.previous:
#             raise Exception(f'Trying to use {class_name} without a previos step being existent.')
#             or
#             not hasattr(self.previous, 'data')
#             ):
#             raise Exception('Trying to use StoringStep without previos step containing data.')
#         elif not self.previous.data:
#
#             raise Exception(f'{class_name} did not provide valid data attribute.')
#         else:
#             return self.previous.data



# class StoringStep(Chain):
#     def __init__(self, storage: StorageMethod):
#         self.storage = storage
#
#     def _process_forward(self):
#         if (not self.previous or
#             not hasattr(self.previous, 'data') or
#             not self.previous
#             ):
#             if self.previous:
#                 class_name = self.previous.__class__.__name__
#                 raise Exception(f'{class_name} did not provide valid data attribute.')
#             else:
#                 raise Exception('Trying to use StoringStep without previos step containing data.')
#         # now, storing from previous data should be OK:
#         self.storage.store(self.previous.data)
#
#     def _process_backward(self):
#         self.data = self.storage.load()
#
# class LoadingStep(RevertedStep):
#     def __init__(self, storage: StorageMethod):
#         super().__init__(chain = StoringStep(storage=storage))
#
# class StoreLoadChain(StoringStep):
#     def __init__(self, storing_method: StorageMethod, loading_method: StorageMethod):
#         super().__init__(storage = storing_method)
#         self.append(LoadingStep(storage = loading_method))
#
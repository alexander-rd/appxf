from copy import deepcopy

class Buffer(): 
    '''Helper to organize data buffering. 
    
    Domain: The buffer is intended to be used for a domain of data. The domain
    name assigned at initialization is used to persist the data buffer to re-use
    it's content on the next application execution.
    
    What plus input: When you store or retrieve data, you pass "what (type of)
    data" and the corresponding input (as string). Splitting the "what" is done
    to allow a reset of a specific type of data (later). Note that having the
    input as simple string makes this class flexible but limits it's usage to
    "simple" inputs.
    
    Independent copies. Implementation ensures that the current version of data
    is stored and later changes to data are not reflected in buffer. Also, when
    returning the buffer, it will return an independent copy.
    '''
    
    def __init__(self, name='default', storageDir='./data/buffer'):
        self.name=name
        self.storageDir=storageDir
        self.buffer = dict()
        
    def getData(self, what, input=''):
        '''Get data from buffer for what(input).'''
        if what in self.buffer.keys():
            if input in self.buffer[what].keys():
                return deepcopy(self.buffer[what][input])
        # what(input) not not returned above: returned above:nd (we did not return above already)
        return None
            
    
    def setData(self, data, what, input=''):
        '''Set data to buffer for what(input). This will overwrite existing data.'''
        if not what in self.buffer.keys():
            self.buffer[what] = dict()
        self.buffer[what][input] = deepcopy(data)
    
    def clearData(self):
        self.buffer = dict()
        
    def persist(self):
        raise Exception("Not yet implemented!")
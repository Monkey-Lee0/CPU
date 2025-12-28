from assassyn.frontend import *

class ICache(Module):
    def __init__(self, cacheSize: int):
        self.cacheSize = cacheSize
        self.cachePool = RegArray(Bits(32), self.cacheSize)
        self.validNum = Bits(32)(0)
        super().__init__(ports={
            'start':Port(Bits(1))
        })

    @module.combinational
    def build(self, decoder, decoderValid):
        start = self.start.peek()
        with Condition(start):
            pass
            # TODO
            # readIn = self.validNum < Bits(32)(self.cacheSize)
            # moveOut = decoderValid & (self.validNum > Bits(32)(0))
            # with Condition(readIn & moveOut):
            #     for i in range(self.cacheSize - 1):
            #         (self.cachePool & self)[i] <= self.cachePool[i+1]
            #     self.cachePool[self.cacheSize - 1] <= self.validNum

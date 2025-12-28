from assassyn.frontend import *

class ICache(Module):
    def __init__(self, cacheSize: int, init_file):
        self.cacheSize = cacheSize
        self.cachePool = RegArray(Bits(32), self.cacheSize)
        self.validNum = Bits(32)(0)
        self.sram = SRAM(32, 16384, init_file)
        super().__init__(ports={
            'start':Port(Bits(1)),
        })

    @module.combinational
    def build(self, decoder, decoderValid):
        pass
        pc = RegArray(Bits(32), 1)
        start = self.start.peek()
        re = RegArray(Bits(1), 1, initializer=[1])
        self.sram.build(Bits(1)(0), re[0], pc[0], Bits(32)(0))
        with Condition(start):
            newValidNum = self.validNum - decoderValid[0].zext(Bits(32))
            full = newValidNum == Bits(32)(self.cacheSize)
            with Condition(~full): # not full
                self.validNum <= newValidNum + Bits(32)(1)
                (self.cachePool & self)[newValidNum] <= self.sram.dout[0]
                log("{}", self.sram.dout[0])
                (pc & self)[0] <= pc[0] + Bits(32)(4)
            with Condition(full):
                self.validNum <= newValidNum
            (re & self)[0] <= (~full) # read when not full

            with Condition(decoderValid[0]):
                for i in range(self.cacheSize - 1):
                    with Condition(Bits(32)(i) < self.validNum):
                        (self.cachePool & self)[i] <= self.cachePool[i+1]
                decoder.instruction.push(self.cachePool[0])

        decoder.async_called()

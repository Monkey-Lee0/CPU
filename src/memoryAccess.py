from assassyn.frontend import *
from decoder import *
from utils import ValArray

class ICache(Module):
    def __init__(self, cacheSize: int, init_file):
        self.cacheSize = cacheSize
        self.cachePool = ValArray(Bits(32), cacheSize, self)
        self.id = ValArray(Bits(32), cacheSize, self)
        self.sram = SRAM(32, 16384, init_file)
        super().__init__(ports={
            'start':Port(Bits(1)),
        })

    @module.combinational
    def build(self):
        pc = RegArray(Bits(32), 1)
        pc_cache = RegArray(Bits(32), 1)
        start = self.start.peek()
        re = RegArray(Bits(1), 1, initializer=[1])
        self.sram.build(Bits(1)(0), re[0], pc_cache[0], Bits(32)(0))
        lastInst = RegArray(Bits(32), 1)

        clk = RegArray(Bits(32), 1)
        (clk & self)[0] <= clk[0] + Bits(32)(1)
        valid = clk[0][1:1] == Bits(1)(0)

        with Condition(start):
            hasValue = (self.sram.dout[0] != Bits(32)(0)) & (self.sram.dout[0] != lastInst[0])
            cnt = Bits(32)(0)
            inst = Bits(32)(0)
            for i in range(self.cacheSize):
                zero = self.id[i].get() == Bits(32)(0)
                changeInst = (self.id[i].get() == pc[0] + Bits(32)(1)) & valid
                # log('!!! {} {} {} {}', Bits(32)(i), changeInst, self.cachePool[i][1][0], self.cachePool[i][0][0])
                inst = changeInst.select(self.cachePool[i].get(), inst)

                newValue0 = self.cachePool[i].get()
                newValue0 = (zero & hasValue).select(self.sram.dout[0], newValue0)
                newValue0 = changeInst.select(Bits(32)(0), newValue0)
                self.cachePool[i] <= newValue0

                newValue1 = self.id[i].get()
                newValue1 = (zero & hasValue).select(pc_cache[0], newValue1)
                newValue1 = changeInst.select(Bits(32)(0), newValue1)
                self.id[i] <= newValue1

                cnt = zero.select(cnt, cnt + Bits(32)(1))
                hasValue = zero.select(Bits(1)(0), hasValue)

            with Condition(self.sram.dout[0] != Bits(32)(0)):
                (lastInst & self)[0] <= self.sram.dout[0]
            (re & self)[0] <= (cnt <= Bits(32)(self.cacheSize - 1))
            (pc_cache & self)[0] <= pc_cache[0] + (cnt <= Bits(32)(self.cacheSize - 1))
            (pc & self)[0] <= pc[0] + (inst != Bits(32)(0))

            with Condition(inst != Bits(32)(0)):
                # log('{} ???', inst)
                parseInst(inst)
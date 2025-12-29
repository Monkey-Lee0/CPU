from assassyn.frontend import *
from memoryAccess import ICache




data = [0b00000000011000101000000010110011, 0b01000000001000110000001010110011,
        0b00000000101000110100110110110011, 0b00000000011100110011001010110011,
        0b00000000010100101000001010010011, 0b01000000000010010111010010010011,
        0b11111010011000111000100100100011, 0b10111010011100110101110101100011,
        0b00000000110000110101001100010011, 0b01011101110000000000000101101111,
        0b01111010100100001110000010010111,]

class Driver(Module):
    def __init__(self):
        super().__init__({})

    @module.combinational
    def build(self, iCache: ICache):
        flag = RegArray(Bits(1), 1)
        with Condition(flag[0] == Bits(1)(0)):
            log("enter")
            (flag & self)[0] <= Bits(1)(1)
            iCache.start.push(Bits(1)(1))
        iCache.async_called()


def buildSys():
    sys = SysBuilder('CPU')
    with sys:
        driver = Driver()
        iCache = ICache(8, 'workload/test.data')

        driver.build(iCache)
        iCache.build()

    return sys
from assassyn.frontend import *
from memoryAccess import ICache
from rs import RS
from regFile import RegFile
from rob import ROB

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
        iCache = ICache(8, 'workload/hazard.data')
        rs = RS(8)
        rob = ROB(8)
        rf = RegFile(rob)

        driver.build(iCache)
        iCache.build(rs, rob)
        rob.build(rf)
        rs.build(rf)

    return sys
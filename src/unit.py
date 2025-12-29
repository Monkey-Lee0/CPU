from assassyn.frontend import *
from memoryAccess import ICache
from rs import RS
from regFile import RegFile
from rob import ROB
from alu import ALU

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
        alu = ALU()

        driver.build(iCache)

        a_flushTag = rob.build(rf, rs)
        alu.build(rob)
        rs.build(rf, alu,a_flushTag)
        iCache.build(rs, rob,a_flushTag)

    return sys
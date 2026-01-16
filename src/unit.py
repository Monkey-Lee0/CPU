from assassyn.frontend import *
from memoryAccess import ICache, DCache
from rs import RS
from regFile import RegFile
from rob import ROB
from alu import ALU, AGU
from lsb import LSB

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


def buildSys(testcase):
    sys = SysBuilder('CPU')
    with sys:
        driver = Driver()
        iCache = ICache(8, f'workload/{testcase}.data')
        dCache = DCache(32, 'workload/dcache.in')
        rs = RS(8)
        rob = ROB(8)
        rf = RegFile(rob)
        alu = ALU()
        agu = AGU()
        lsb = LSB(8)

        driver.build(iCache)
        iCache.build(rs, rob, lsb, rf)
        dCache.build()
        rs.build(rf, lsb, alu, agu)
        rob.build(rf, iCache, rs, lsb, alu)
        alu.build(rob)
        agu.build(lsb)
        lsb.build(dCache, rob)

    return sys
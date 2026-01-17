import contextlib

from assassyn.frontend import *
from rob import ROB
from utils import popAllPorts, ValArray

def calc_pos(Val:Value):
    res = Bits(32)(0)
    for i in range(32):
        res = res.select(Val > Bits(32)(1 << i)).select(res + Bits(32)(1), res)
    return res + Bits(32)(1)
def calc_abs():
    pass
def calc_delta(Val1,Val2):
    res = (Val1 > Val2).select(Val1 - Val2, Bits(32)(0))
    return res

class ALU(Module):
    def __init__(self):
        super().__init__(ports={
            'instId':Port(Bits(32)),
            'lhs':Port(Bits(32)),
            'rhs':Port(Bits(32)),
            'robId':Port(Bits(32)),
            'flushTag':Port(Bits(1))
        })
        self.busy = ValArray(Bits(1), 1, self)
        self.inst = ValArray(Bits(32), 1, self)
        self.lhsV = ValArray(Bits(32), 1, self)
        self.rhsV = ValArray(Bits(32), 1, self)
        self.robIdV = ValArray(Bits(32), 1, self)
        self.bitPos = ValArray(Bits(32), 1, self)
        self.lhsPos = ValArray(Bits(32), 1, self)
        self.rhsPos = ValArray(Bits(32), 1, self)
        self.res = ValArray(Bits(32), 1, self)

    @module.combinational
    def build(self,rob:ROB):
        flush = self.flushTag.valid()
        with Condition(flush):
            popAllPorts(self)
            self.clear()

        # issue M inst or commit answer of easy inst to rob
        with Condition((~flush) & self.instId.valid()):
            instId = self.instId.pop()
            lhs = self.lhs.pop()
            rhs = self.rhs.pop()
            robId = self.robId.pop()
            res = instId.case({
                Bits(32)(1): lhs + rhs,
                Bits(32)(2): lhs - rhs,
                Bits(32)(3): lhs & rhs,
                Bits(32)(4): lhs | rhs,
                Bits(32)(5): lhs ^ rhs,
                Bits(32)(6): lhs << rhs,
                Bits(32)(7): lhs >> rhs,
                Bits(32)(8): (lhs.bitcast(Int(32)) >> rhs).bitcast(Bits(32)),
                Bits(32)(9): (lhs.bitcast(Int(32)) < rhs.bitcast(Int(32))).zext(Bits(32)),
                Bits(32)(10): (lhs < rhs).zext(Bits(32)),
                Bits(32)(11): lhs + rhs,
                Bits(32)(12): lhs & rhs,
                Bits(32)(13): lhs | rhs,
                Bits(32)(14): lhs ^ rhs,
                Bits(32)(15): lhs << rhs,
                Bits(32)(16): lhs >> rhs,
                Bits(32)(17): (lhs.bitcast(Int(32)) >> rhs).bitcast(Bits(32)),
                Bits(32)(18): (lhs.bitcast(Int(32)) < rhs.bitcast(Int(32))).zext(Bits(32)),
                Bits(32)(19): (lhs < rhs).zext(Bits(32)),
                Bits(32)(20): lhs + rhs,
                Bits(32)(21): lhs + rhs,
                Bits(32)(22): lhs + rhs,
                Bits(32)(23): lhs + rhs,
                Bits(32)(24): lhs + rhs,
                Bits(32)(25): lhs + rhs,
                Bits(32)(26): lhs + rhs,
                Bits(32)(27): lhs + rhs,
                Bits(32)(28): (lhs == rhs).zext(Bits(32)),
                Bits(32)(29): (lhs.bitcast(Int(32)) >= rhs.bitcast(Int(32))).zext(Bits(32)),
                Bits(32)(30): (lhs >= rhs).zext(Bits(32)),
                Bits(32)(31): (lhs.bitcast(Int(32)) < rhs.bitcast(Int(32))).zext(Bits(32)),
                Bits(32)(32): (lhs < rhs).zext(Bits(32)),
                Bits(32)(33): (lhs != rhs).zext(Bits(32)),
                Bits(32)(35): lhs + rhs,
                Bits(32)(36): lhs + (rhs << Bits(32)(12)),
                Bits(32)(37): rhs << Bits(32)(12),
                None: Bits(32)(0)
            })
            self.busy[0] = (instId > Bits(32)(37)).select(Bits(1)(1), self.busy[0])
            self.lhsV[0] = (instId > Bits(32)(37)).select(lhs, self.lhsV[0])
            self.rhsV[0] = (instId > Bits(32)(37)).select(rhs, self.rhsV[0])
            self.robIdV[0] = (instId > Bits(32)(37)).select(robId, self.robIdV[0])
            self.instIdV[0] = (instId > Bits(32)(37)).select(instId, self.instIdV[0])
            pos1 = calc_pos(lhs)
            pos2 = calc_pos(rhs)
            self.lhsPos[0] = (instId > Bits(32)(37)).select(pos1, self.lhsPos[0])
            self.rhsPos[0] = (instId > Bits(32)(37)).select(pos2, self.rhsPos[0])
            self.bitPos[0] = (instId > Bits(32)(37)).select(calc_delta(pos1, pos2), self.bitPos[0])

            # directly modify in rob
            with Condition(Bits(32)(37) >= instId):
                for i in range(rob.robSize):
                    with Condition(rob.ID[i] == robId):
                        rob.busy[i] = Bits(1)(0)
                        with Condition(rob.inst[i] == Bits(32)(35)):
                            rob.anotherPC[i] = res
                        with Condition(rob.inst[i] != Bits(32)(35)):
                            rob.value[i] = res
        # div and rem
        with Condition((~flush) & (self.busy[0] != Bits(1)(0)) & instId >= Bits(32)(42)):
            with Condition(self.lhsPos[0] > self.rhsPos[0]):
                ls_rhs = self.rhsV[0] << self.bitPos[0]
                bit_res = (ls_rhs < self.lhsV[0]).select(Bits(32)(1),Bits(32)(0))
                res_lhs = (ls_rhs < self.lhsV[0]).select(self.lhsV[0] - ls_rhs, self.lhsV[0])
                lPos = calc_pos(res_lhs)
                self.lhsPos[0] = res_lhs
                self.res[0] = self.res[0] | (bit_res << self.bitPos[0])
                self.bitPos[0] = calc_delta(lPos , self.rhsPos[0])
            with Condition(self.lhsPos[0] == self.rhsPos[0]):
                bit_res = (self.rhsV[0] < self.lhsV[0]).select(Bits(32)(1), Bits(32)(0))
                res_lhs = (self.rhsV[0] < self.lhsV[0]).select(self.lhsV[0] - ls_rhs, self.lhsV[0])
                ultimate_res =  self.res[0] | bit_res
                for i in range(rob.robSize):
                    with Condition(rob.ID[i] == robId):
                        rob.busy[i] = Bits(1)(0)
                        with Condition(rob.inst[i] == Bits(32)(42)):
                            rob.value[i] = ultimate_res
                        with Condition(rob.inst[i] == Bits(32)(43)):
                            rob.value[i] = ultimate_res
                        with Condition(rob.inst[i] == Bits(32)(44)):
                            rob.value[i] = res_lhs
                        with Condition(rob.inst[i] == Bits(32)(45)):
                            rob.value[i] = res_lhs
            with Condition(self.lhsPos[0] < self.rhsPos[0]):
                for i in range(rob.robSize):
                    with Condition(rob.ID[i] == robId):
                        rob.busy[i] = Bits(1)(0)
                        with Condition(rob.inst[i] == Bits(32)(42)):
                            rob.value[i] = self.res[0]
                        with Condition(rob.inst[i] == Bits(32)(43)):
                            rob.value[i] = self.res[0]
                        with Condition(rob.inst[i] == Bits(32)(44)):
                            rob.value[i] = self.lhsV[0]
                        with Condition(rob.inst[i] == Bits(32)(45)):
                            rob.value[i] = self.lhsV[0]



    def clear(self):
        self.busy = Bits(1)(0)
        self.instIdV = Bits(32)(0)
        self.lhsV = Bits(32)(0)
        self.rhsV = Bits(32)(0)
        self.robIdV = Bits(32)(0)
        self.status = Bits(32)(0)
        # clear是否要把tag归零?

class AGU(Module):
    def __init__(self):
        super().__init__(ports={
            'lhs':Port(Bits(32)),
            'rhs':Port(Bits(32)),
            'robId':Port(Bits(32))
        })
    @module.combinational
    def build(self, lsb):
        with Condition(self.robId.valid()):
            lhs = self.lhs.pop()
            rhs = self.rhs.pop()
            robId = self.robId.pop()
            lsb.newId_agu.push(robId)
            lsb.newAddr.push(lhs + rhs)
            log("{}: {} + {} = {}", robId, lhs, rhs, lhs + rhs)
        lsb.async_called()
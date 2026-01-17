import contextlib

from assassyn.frontend import *
from rob import ROB
from utils import popAllPorts, ValArray
from decoder import takeBitsRange

def isMul(inst):
    return (inst >= Bits(32)(38)) & (Bits(32)(41) >= inst)

def isDivOrRem(inst):
    return inst >= Bits(32)(42)

def Adder3_2(A, B, C):
    return A^B^C, ((A & B) | ((A ^ B) & C)) << Bits(64)(1)

def isNeg(val: Value):
    return val >= Bits(32)(1<<31)

def calc_abs(val: Value):
    return isNeg(val).select((~val) + Bits(32)(1), val)

def calc_delta(Val1,Val2):
    res = (Val1 > Val2).select(Val1 - Val2, Bits(32)(0))
    return res

class ALU(Module):
    def __init__(self):
        super().__init__(ports={
            'instId':Port(Bits(32)),
            'lhs':Port(Bits(32)),
            'rhs':Port(Bits(32)),
            'newId':Port(Bits(32)),
            'flushTag':Port(Bits(1))
        })
        self.busy = ValArray(Bits(1), 1, self)
        self.inst = ValArray(Bits(32), 1, self)
        self.robId = ValArray(Bits(32), 1, self)
        self.lhsV = ValArray(Bits(32), 1, self)
        self.rhsV = ValArray(Bits(32), 1, self)

        self.sign = ValArray(Bits(1), 1, self)

        # status for multiplication
        self.countOfPartial = ValArray(Bits(32), 1, self)
        self.partial = ValArray(Bits(64), 33, self)

        # status for division & remain
        self.divVal = ValArray(Bits(64), 1, self)
        self.baseVal = ValArray(Bits(32), 1, self)
        self.bitPos = ValArray(Bits(32), 1, self)
        self.res = ValArray(Bits(32), 1, self)

    @module.combinational
    def build(self,rob:ROB):
        flush = self.flushTag.valid()
        with Condition(flush):
            popAllPorts(self)
            self.busy[0] = Bits(1)(0)

        # issue M inst or commit answer of easy inst to rob
        with (Condition((~self.busy[0]) & (~flush) & self.newId.valid())):
            instId = self.instId.pop()
            lhs = self.lhs.pop()
            rhs = self.rhs.pop()
            robId = self.newId.pop()
            self.inst[0] = instId
            self.robId[0] = robId
            self.lhsV[0] = lhs
            self.rhsV[0] = rhs
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

            # directly modify in rob
            with Condition(Bits(32)(37) >= instId):
                for i in range(rob.robSize):
                    with Condition(rob.ID[i] == robId):
                        rob.busy[i] = Bits(1)(0)
                        with Condition(rob.inst[i] == Bits(32)(35)):
                            rob.anotherPC[i] = res
                        with Condition(rob.inst[i] != Bits(32)(35)):
                            rob.value[i] = res
                log("{}: {} {} {} = {}", robId, lhs, instId, rhs, res)

            # issue mul
            with Condition(isMul(instId)):
                A = (Bits(32)(40) >= instId).select(calc_abs(lhs), lhs)
                B = (Bits(32)(39) >= instId).select(calc_abs(rhs), rhs)
                self.sign[0] = (Bits(32)(40) >= instId).select(isNeg(lhs), Bits(1)(0)) ^ \
                        (Bits(32)(39) >= instId).select(isNeg(rhs), Bits(1)(0))
                self.countOfPartial[0] = Bits(32)(32)
                for i in range(32):
                    self.partial[i] = B[i:i].select(A.bitcast(Bits(64)) << Bits(64)(i), Bits(64)(0))
                self.busy[0] = Bits(1)(1)

            # issue div & rem
            with Condition(isDivOrRem(instId)):
                self.sign[0] = instId.case({
                    Bits(32)(42): isNeg(lhs) ^ isNeg(rhs),
                    Bits(32)(44): isNeg(rhs),
                    None: Bits(1)(0)
                })
                self.divVal[0] = ((instId & Bits(32)(1)) == Bits(32)(0)).select(calc_abs(lhs), lhs).bitcast(Bits(64))
                self.baseVal[0] = ((instId & Bits(32)(1)) == Bits(32)(0)).select(calc_abs(rhs), rhs)
                self.busy[0] = Bits(1)(1)
                self.res[0] = Bits(32)(0)
                self.bitPos[0] = Bits(32)(32)

        with Condition(self.busy[0] & (~flush) & isMul(self.inst[0])):
            # solve mul(Wallace Tree)
            with Condition(self.countOfPartial[0] >= Bits(32)(3)):
                newCount = Bits(32)(0)
                simulateCount = 0
                for i in range(2, 33, 3):
                    with Condition(self.countOfPartial[0] > Bits(32)(i)):
                        res1, res2 = Adder3_2(self.partial[i], self.partial[i-1], self.partial[i-2])
                        self.partial[simulateCount] = res1
                        self.partial[simulateCount + 1] = res2
                    with Condition(self.countOfPartial[0] == Bits(32)(i-1)):
                        self.partial[simulateCount] = self.partial[i-2]
                    with Condition(self.countOfPartial[0] == Bits(32)(i)):
                        self.partial[simulateCount] = self.partial[i-2]
                        self.partial[simulateCount + 1] = self.partial[i-1]

                    newCount = newCount + ((self.countOfPartial[0] > Bits(32)(i-1)).select(Bits(32)(1), Bits(32)(0)) + (
                            self.countOfPartial[0] > Bits(32)(i - 2)).select(Bits(32)(1), Bits(32)(0)))
                    simulateCount = simulateCount + 2

                self.countOfPartial[0] = newCount

            # final add
            with Condition(self.countOfPartial[0] == Bits(32)(2)):
                res = self.partial[0] + self.partial[1]
                res = self.sign[0].select((~res) + Bits(64)(1), res)
                self.busy[0] = Bits(1)(0)
                for i in range(rob.robSize):
                    with Condition(rob.ID[i] == self.robId[0]):
                        rob.busy[i] = Bits(1)(0)
                        with Condition(self.inst[0] == Bits(32)(38)):
                            rob.value[i] = (res & (Bits(64)(0xFFFFFFFF))).bitcast(Bits(32))
                        with Condition(self.inst[0] != Bits(32)(38)):
                            rob.value[i] = (res >> Bits(64)(32)).bitcast(Bits(32))
                log("{}: {} {} {} = {}", self.robId[0], self.lhsV[0], self.inst[0], self.rhsV[0], res)

        # div and rem
        with Condition(self.busy[0] & (~flush) & isDivOrRem(self.inst[0])):
            with Condition(self.bitPos[0] >= Bits(32)(1)):
                A = self.divVal[0]
                B = self.baseVal[0].bitcast(Bits(64))
                pos = self.bitPos[0] - Bits(32)(1)
                res = self.res[0]
                movedB = B << pos
                self.bitPos[0] = pos
                with Condition(A >= movedB):
                    self.divVal[0] = A - movedB
                    self.res[0] = res + (Bits(32)(1) << pos)
            with Condition(self.bitPos[0] == Bits(32)(0)):
                res = (Bits(32)(43) >= self.inst[0]).select(self.res[0], self.divVal[0].bitcast(Bits(32)))
                res = self.sign[0].select((~res) + Bits(32)(1), res)
                self.busy[0] = Bits(1)(0)
                for i in range(rob.robSize):
                    with Condition(rob.ID[i] == self.robId[0]):
                        rob.busy[i] = Bits(1)(0)
                        rob.value[i] = res
                log("{}: {} {} {} = {}", self.robId[0], self.lhsV[0], self.inst[0], self.rhsV[0], res)

class AGU(Module):
    def __init__(self):
        super().__init__(ports={
            'lhs':Port(Bits(32)),
            'rhs':Port(Bits(32)),
            'newId':Port(Bits(32))
        })
    @module.combinational
    def build(self, lsb):
        with Condition(self.newId.valid()):
            lhs = self.lhs.pop()
            rhs = self.rhs.pop()
            robId = self.newId.pop()
            lsb.newId_agu.push(robId)
            lsb.newAddr.push(lhs + rhs)
            log("{}: {} + {} = {}", robId, lhs, rhs, lhs + rhs)
        lsb.async_called()
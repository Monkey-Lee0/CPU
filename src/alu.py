from assassyn.frontend import *
from rob import ROB

class ALU(Module):
    def __init__(self):
        super().__init__(ports={
            'instId':Port(Bits(32)),
            'lhs':Port(Bits(32)),
            'rhs':Port(Bits(32)),
            'robId':Port(Bits(32))
        })
    @module.combinational
    def build(self,rob:ROB):
        with Condition(self.instId.valid()):
            instId = self.instId.pop()
            lhs = self.lhs.pop()
            rhs = self.rhs.pop()
            robId = self.robId.pop()
            res = instId.case({
                Bits(32)(1):lhs + rhs,
                Bits(32)(2):lhs - rhs,
                Bits(32)(3):lhs & rhs,
                Bits(32)(4):lhs | rhs,
                Bits(32)(5):lhs ^ rhs,
                Bits(32)(6):lhs << rhs,
                Bits(32)(7):lhs >> rhs,
                Bits(32)(8):(lhs.bitcast(Int(32)) >> rhs).bitcast(Bits(32)),
                Bits(32)(9):(lhs.bitcast(Int(32)) < rhs.bitcast(Int(32))).zext(Bits(32)),
                Bits(32)(10):(lhs < rhs).zext(Bits(32)),
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
                # TODO
                Bits(32)(37): rhs << Bits(32)(12),
                None: Bits(32)(0)
            })
            rob.resFromALU.push(res)
            rob.idFromALU.push(robId)

            log("{} {} {} = {}", lhs, instId, rhs, res)





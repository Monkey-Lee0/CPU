from assassyn.frontend import *
from utils import ValArray

class ROB(Module):
    def __init__(self, robSize):
        super().__init__(ports={
            'type':Port(Bits(32)),
            'id':Port(Bits(32)),
            'rd':Port(Bits(32)),
            'rs1':Port(Bits(32)),
            'rs2':Port(Bits(32)),
            'imm':Port(Bits(32)),
            'newId':Port(Bits(32)),
            'resFromALU':Port(Bits(32)),
            'idFromALU':Port(Bits(32))
        })
        self.robSize = robSize
        self.busy = ValArray(Bits(1), robSize, self)
        self.inst = ValArray(Bits(32), robSize, self)
        self.dest = ValArray(Bits(32), robSize, self)
        self.value = ValArray(Bits(32), robSize, self)

    @module.combinational
    def build(self, rf):
        we = RegArray(Bits(1), 2)
        wPos = RegArray(Bits(32), 2)
        wData = RegArray(Bits(32), 2)
        wId = RegArray(Bits(32), 2)

        # issue in rob
        with Condition(self.type.valid()):
            instType = self.type.pop()
            instId = self.id.pop()
            rd = self.rd.pop()
            rs1 = self.rs1.pop()
            rs2 = self.rs2.pop()
            imm = self.imm.pop()
            newId = self.newId.pop()

            with Condition(rd != Bits(32)(0)):
                rf.build(rd, rf.regs[rd], newId)

        rf.log()
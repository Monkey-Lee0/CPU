from assassyn.frontend import *
from utils import ValArray

class RS(Module):
    def __init__(self, itemSize):
        super().__init__(ports={
            'type':Port(Bits(32)),
            'id':Port(Bits(32)),
            'rd':Port(Bits(32)),
            'rs1':Port(Bits(32)),
            'rs2':Port(Bits(32)),
            'imm':Port(Bits(32))
        })

        self.itemSize = itemSize
        self.busy = ValArray(Bits(1), itemSize, self)
        self.op = ValArray(Bits(32), itemSize, self)
        self.vj = ValArray(Bits(32), itemSize, self)
        self.vk = ValArray(Bits(32), itemSize, self)
        self.qj = ValArray(Bits(32), itemSize, self)
        self.qk = ValArray(Bits(32), itemSize, self)
        self.dest = ValArray(Bits(32), itemSize, self)
        self.A = ValArray(Bits(32), itemSize, self)

    @module.combinational
    def build(self):
        with Condition(self.type.valid()):
            instType = self.type.pop()
            instId = self.id.pop()
            rd = self.rd.pop()
            rs1 = self.rs1.pop()
            rs2 = self.rs2.pop()
            imm = self.imm.pop()
            tag = Bits(1)(1)
            for i in range(self.itemSize):
                with Condition((~self.busy[i].get()) & tag):
                    self.busy[i] <= Bits(1)(1)
                    self.op[i] <= instId
                    self.vj[i] <= rs1
                    self.vk[i] <= rs2
                    self.dest[i] <= rd
                    self.A[i] <= imm
                tag = tag & self.busy[i].get()
            log('{} {} {} {} {} {}', instType, instId, rd, rs1, rs2, imm)

        self.printTable()

    def printTable(self):
        log('-'*50)
        for i in range(self.itemSize):
            log('{} {} {} {} {} {} {} {}', self.busy[i].get(), self.op[i].get(), self.vj[i].get(),
                self.vk[i].get(), self.qj[i].get(), self.qk[i].get(), self.dest[i].get(), self.A[i].get())
        log('-'*50)
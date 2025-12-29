from regFile import *
from utils import ValArray

class RS(Module):
    def __init__(self, rsSize):
        super().__init__(ports={
            'type':Port(Bits(32)),
            'id':Port(Bits(32)),
            'rd':Port(Bits(32)),
            'rs1':Port(Bits(32)),
            'rs2':Port(Bits(32)),
            'imm':Port(Bits(32)),
            'newId':Port(Bits(32))
        })

        self.itemSize = rsSize
        self.busy = ValArray(Bits(1), rsSize, self)
        self.op = ValArray(Bits(32), rsSize, self)
        self.vj = ValArray(Bits(32), rsSize, self)
        self.vk = ValArray(Bits(32), rsSize, self)
        self.qj = ValArray(Bits(32), rsSize, self)
        self.qk = ValArray(Bits(32), rsSize, self)
        self.dest = ValArray(Bits(32), rsSize, self)
        self.A = ValArray(Bits(32), rsSize, self)

    @module.combinational
    def build(self, rf):
        with Condition(self.type.valid()):
            # issue into rs
            instType = self.type.pop()
            instId = self.id.pop()
            rd = self.rd.pop()
            rs1 = self.rs1.pop()
            rs2 = self.rs2.pop()
            imm = self.imm.pop()
            newId = self.newId.pop()

            tag = Bits(1)(1)
            for i in range(self.itemSize):
                with Condition((~self.busy[i].get()) & tag):
                    # type R
                    with Condition(instType == Bits(32)(1)):
                        self.busy[i] <= Bits(1)(1)
                        self.op[i] <= instId
                        self.vj[i] <= (rf.dependence[rs1] != Bits(32)(0)).select(Bits(32)(0), rf.regs[rs1])
                        self.vk[i] <= (rf.dependence[rs2] != Bits(32)(0)).select(Bits(32)(0), rf.regs[rs2])
                        self.qj[i] <= (rf.dependence[rs1] != Bits(32)(0)).select(rf.dependence[rs1], Bits(32)(0))
                        self.qk[i] <= (rf.dependence[rs2] != Bits(32)(0)).select(rf.dependence[rs2], Bits(32)(0))
                        self.dest[i] <= newId
                        self.A[i] <= Bits(32)(0)
                    # type I
                    with Condition(instType == Bits(32)(2)):
                        self.busy[i] <= Bits(1)(1)
                        self.op[i] <= instId
                        self.vj[i] <= (rf.dependence[rs1] != Bits(32)(0)).select(Bits(32)(0), rf.regs[rs1])
                        self.vk[i] <= Bits(32)(0)
                        self.qj[i] <= (rf.dependence[rs1] != Bits(32)(0)).select(rf.dependence[rs1], Bits(32)(0))
                        self.qk[i] <= Bits(32)(0)
                        self.dest[i] <= newId
                        self.A[i] <= imm
                tag = tag & self.busy[i].get()

        self.printTable()

    def printTable(self):
        log('-'*50)
        for i in range(self.itemSize):
            log('busy:{} op:{} vj:{} vk:{} qj:{} qk:{} dest:{} A:{}', self.busy[i].get(), self.op[i].get(),
                self.vj[i].get(), self.vk[i].get(), self.qj[i].get(), self.qk[i].get(), self.dest[i].get(),
                self.A[i].get())
        log('-'*50)
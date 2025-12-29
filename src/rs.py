from regFile import *
from utils import ValArray
from inst import idToType

class RS(Module):
    def __init__(self, rsSize):
        super().__init__(ports={
            'type':Port(Bits(32)),
            'id':Port(Bits(32)),
            'rd':Port(Bits(32)),
            'rs1':Port(Bits(32)),
            'rs2':Port(Bits(32)),
            'imm':Port(Bits(32)),
            'newId':Port(Bits(32)),
            'robId':Port(Bits(32)),
            'robRes':Port(Bits(32))
        })

        self.itemSize = rsSize
        self.busy = ValArray(Bits(1), rsSize, self)
        self.inst = ValArray(Bits(32), rsSize, self)
        self.vj = ValArray(Bits(32), rsSize, self)
        self.vk = ValArray(Bits(32), rsSize, self)
        self.qj = ValArray(Bits(32), rsSize, self)
        self.qk = ValArray(Bits(32), rsSize, self)
        self.dest = ValArray(Bits(32), rsSize, self)
        self.A = ValArray(Bits(32), rsSize, self)

    @module.combinational
    def build(self, rf, alu):
        # issue into rs
        with Condition(self.type.valid()):
            instType = self.type.pop()
            instId = self.id.pop()
            rd = self.rd.pop()
            rs1 = self.rs1.pop()
            rs2 = self.rs2.pop()
            imm = self.imm.pop()
            newId = self.newId.pop()

            tag = Bits(1)(1)
            for i in range(self.itemSize):
                with Condition((~self.busy[i]) & tag):
                    # type R
                    with Condition(instType == Bits(32)(1)):
                        self.busy[i] = Bits(1)(1)
                        self.inst[i] = instId
                        self.vj[i] = (rf.dependence[rs1] != Bits(32)(0)).select(Bits(32)(0), rf.regs[rs1])
                        self.vk[i] = (rf.dependence[rs2] != Bits(32)(0)).select(Bits(32)(0), rf.regs[rs2])
                        self.qj[i] = (rf.dependence[rs1] != Bits(32)(0)).select(rf.dependence[rs1], Bits(32)(0))
                        self.qk[i] = (rf.dependence[rs2] != Bits(32)(0)).select(rf.dependence[rs2], Bits(32)(0))
                        self.dest[i] = newId
                        self.A[i] = Bits(32)(0)
                    # type I
                    with Condition(instType == Bits(32)(2)):
                        self.busy[i] = Bits(1)(1)
                        self.inst[i] = instId
                        self.vj[i] = (rf.dependence[rs1] != Bits(32)(0)).select(Bits(32)(0), rf.regs[rs1])
                        self.vk[i] = Bits(32)(0)
                        self.qj[i] = (rf.dependence[rs1] != Bits(32)(0)).select(rf.dependence[rs1], Bits(32)(0))
                        self.qk[i] = Bits(32)(0)
                        self.dest[i] = newId
                        self.A[i] = imm
                tag = tag & self.busy[i]

        # forward into alu
        tag = Bits(1)(1)
        for i in range(self.itemSize):
            canExecute = self.busy[i] & (self.qj[i] == Bits(32)(0)) & (self.qk[i] == Bits(32)(0))
            with Condition(tag & canExecute):
                instType = idToType(self.inst[i])
                log("{} {} {} {}", Bits(32)(i), canExecute, self.inst[i], instType)
                # type R
                with Condition(instType == Bits(32)(1)):
                    alu.instId.push(self.inst[i])
                    alu.lhs.push(self.vj[i])
                    alu.rhs.push(self.vk[i])
                    alu.robId.push(self.dest[i])
                # type I
                with Condition(instType == Bits(32)(2)):
                    alu.instId.push(self.inst[i])
                    alu.lhs.push(self.vj[i])
                    alu.rhs.push(self.A[i])
                    alu.robId.push(self.dest[i])

                self.busy[i] = Bits(1)(0)
                self.inst[i] = Bits(32)(0)
                self.vj[i] = Bits(32)(0)
                self.vk[i] = Bits(32)(0)
                self.qj[i] = Bits(32)(0)
                self.qk[i] = Bits(32)(0)
                self.dest[i] = Bits(32)(0)
                self.A[i] = Bits(32)(0)
            tag = tag & (~canExecute)

        # update from rob
        with Condition(self.robId.valid()):
            robId = self.robId.pop()
            robRes = self.robRes.pop()
            for i in range(self.itemSize):
                with Condition(self.qj[i] == robId):
                    self.qj[i] <= Bits(32)(0)
                    self.vj[i] <= robRes
                with Condition(self.qk[i] == robId):
                    self.qk[i] <= Bits(32)(0)
                    self.vk[i] <= robRes

        # self.log()
        alu.async_called()

    def log(self):
        log('-'*50)
        for i in range(self.itemSize):
            log('busy:{} op:{} vj:{} vk:{} qj:{} qk:{} dest:{} A:{}', self.busy[i], self.inst[i],
                self.vj[i], self.vk[i], self.qj[i], self.qk[i], self.dest[i],
                self.A[i])
        log('-'*50)
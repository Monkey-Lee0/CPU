from regFile import *
from utils import ValArray, popAllPorts
from inst import idToType

class RS(Module):
    def __init__(self, rsSize):
        super().__init__(ports={
            'inst_type':Port(Bits(32)),
            'id':Port(Bits(32)),
            'rd':Port(Bits(32)),
            'rs1':Port(Bits(32)),
            'rs2':Port(Bits(32)),
            'imm':Port(Bits(32)),
            'newId':Port(Bits(32)),
            'flushTag':Port(Bits(1)),
            'robId':Port(Bits(32)),
            'robRes':Port(Bits(32))
        })

        self.rsSize = rsSize
        self.busy = ValArray(Bits(1), rsSize, self)
        self.inst = ValArray(Bits(32), rsSize, self)
        self.vj = ValArray(Bits(32), rsSize, self)
        self.vk = ValArray(Bits(32), rsSize, self)
        self.qj = ValArray(Bits(32), rsSize, self)
        self.qk = ValArray(Bits(32), rsSize, self)
        self.dest = ValArray(Bits(32), rsSize, self)
        self.A = ValArray(Bits(32), rsSize, self)

    def accept(self, robId, value):
        for i in range(self.rsSize):
            with Condition(self.qj[i] == robId):
                self.qj[i] = Bits(32)(0)
                self.vj[i] = value
            with Condition(self.qk[i] == robId):
                self.qk[i] = Bits(32)(0)
                self.vk[i] = value

    @module.combinational
    def build(self, rf, lsb, alu_arr, agu):
        # flush
        flush = self.flushTag.valid()
        with Condition(flush):
            for i in range(self.rsSize):
                self.clear(i)
            popAllPorts(self)

        with Condition(~flush):
            # check robRes(to solve the problem that rob commits and rs issues in the same cycle)
            with Condition(self.robId.valid()):
                robId = self.robId.pop()
                robRes = self.robRes.pop()
                self.accept(robId, robRes)
            # issue into rs
            with Condition(self.inst_type.valid()):
                instType = self.inst_type.pop()
                instId = self.id.pop()
                rd = self.rd.pop()
                rs1 = self.rs1.pop()
                rs2 = self.rs2.pop()
                imm = self.imm.pop()
                newId = self.newId.pop()

                tag = Bits(1)(1)
                for i in range(self.rsSize):
                    with Condition((~self.busy[i]) & tag):
                        # type R
                        with Condition(instType == Bits(32)(1)):
                            self.busy[i] = Bits(1)(1)
                            self.inst[i] = instId
                            self.vj[i] = ((rf.dependence[rs1] != Bits(32)(0)) & (rf.dependence[rs1] != newId)).select(Bits(32)(0), rf.regs[rs1])
                            self.vk[i] = ((rf.dependence[rs2] != Bits(32)(0)) & (rf.dependence[rs2] != newId)).select(Bits(32)(0), rf.regs[rs2])
                            self.qj[i] = ((rf.dependence[rs1] != Bits(32)(0)) & (rf.dependence[rs1] != newId)).select(rf.dependence[rs1], Bits(32)(0))
                            self.qk[i] = ((rf.dependence[rs2] != Bits(32)(0)) & (rf.dependence[rs2] != newId)).select(rf.dependence[rs2], Bits(32)(0))
                            self.dest[i] = newId
                            self.A[i] = Bits(32)(0)
                        # type I/I*
                        with Condition((instType == Bits(32)(2)) | (instType == Bits(32)(3))):
                            self.busy[i] = Bits(1)(1)
                            self.inst[i] = instId
                            self.vj[i] = ((rf.dependence[rs1] != Bits(32)(0)) & (rf.dependence[rs1] != newId)).select(Bits(32)(0), rf.regs[rs1])
                            self.vk[i] = Bits(32)(0)
                            self.qj[i] = ((rf.dependence[rs1] != Bits(32)(0)) & (rf.dependence[rs1] != newId)).select(rf.dependence[rs1], Bits(32)(0))
                            self.qk[i] = Bits(32)(0)
                            self.dest[i] = newId
                            self.A[i] = imm
                        # type S
                        with Condition((instType == Bits(32)(4))):
                            self.busy[i] = Bits(1)(1)
                            self.inst[i] = instId
                            self.vj[i] = ((rf.dependence[rs1] != Bits(32)(0)) & (rf.dependence[rs1] != newId)).select(Bits(32)(0), rf.regs[rs1])
                            self.vk[i] = ((rf.dependence[rs2] != Bits(32)(0)) & (rf.dependence[rs2] != newId)).select(Bits(32)(0), rf.regs[rs2])
                            self.qj[i] = ((rf.dependence[rs1] != Bits(32)(0)) & (rf.dependence[rs1] != newId)).select(rf.dependence[rs1], Bits(32)(0))
                            self.qk[i] = ((rf.dependence[rs2] != Bits(32)(0)) & (rf.dependence[rs2] != newId)).select(rf.dependence[rs2], Bits(32)(0))
                            self.dest[i] = newId
                            self.A[i] = imm
                        # type B
                        with Condition(instType == Bits(32)(5)):
                            self.busy[i] = Bits(1)(1)
                            self.inst[i] = instId
                            self.vj[i] = ((rf.dependence[rs1] != Bits(32)(0)) & (rf.dependence[rs1] != newId)).select(Bits(32)(0), rf.regs[rs1])
                            self.vk[i] = ((rf.dependence[rs2] != Bits(32)(0)) & (rf.dependence[rs2] != newId)).select(Bits(32)(0), rf.regs[rs2])
                            self.qj[i] = ((rf.dependence[rs1] != Bits(32)(0)) & (rf.dependence[rs1] != newId)).select(rf.dependence[rs1], Bits(32)(0))
                            self.qk[i] = ((rf.dependence[rs2] != Bits(32)(0)) & (rf.dependence[rs2] != newId)).select(rf.dependence[rs2], Bits(32)(0))
                            self.dest[i] = newId
                            self.A[i]= Bits(32)(0)
                        # type U (auipc/lui rd label)
                        with Condition(instType == Bits(32)(6)):
                            self.busy[i] = Bits(1)(1)
                            self.inst[i] = instId
                            self.vj[i] = Bits(32)(0)
                            self.vk[i] = Bits(32)(0)
                            self.qj[i] = Bits(32)(0)
                            self.qk[i] = Bits(32)(0)
                            self.dest[i] = newId
                            self.A[i] = imm
                        # type J (jal rd label)
                        with Condition(instType == Bits(32)(7)):
                            self.busy[i] = Bits(1)(1)
                            self.inst[i] = instId
                            self.vj[i] = Bits(32)(0)
                            self.vk[i] = Bits(32)(0)
                            self.qj[i] = Bits(32)(0)
                            self.qk[i] = Bits(32)(0)
                            self.dest[i] = newId
                            self.A[i]= imm
                    tag = tag & self.busy[i]

            # forward into alu
            totalPrevious = Bits(32)(0)
            for i in range(self.rsSize):
                instType = idToType(self.inst[i])
                canExecute = self.busy[i] & (self.qj[i] == Bits(32)(0)) & (self.qk[i] == Bits(32)(0)) & (
                        (instType == Bits(32)(1)) | (instType == Bits(32)(2)) | (instType == Bits(32)(3)) | (instType == Bits(32)(5))) & (
                        (Bits(32)(19) >= self.inst[i]) | (self.inst[i] >= Bits(32)(28)))
                hasForward = Bits(1)(0)
                for j in range(8):
                    count = Bits(32)(0)
                    for k in range(j):
                        count = count + (~alu_arr[k].busy[0])
                    with Condition(canExecute & (~alu_arr[j].busy[0]) & (~hasForward) & (count == totalPrevious)):
                        # type R
                        with Condition(instType == Bits(32)(1)):
                            alu_arr[j].instId.push(self.inst[i])
                            alu_arr[j].lhs.push(self.vj[i])
                            alu_arr[j].rhs.push(self.vk[i])
                            alu_arr[j].newId.push(self.dest[i])
                        # type I/I*
                        with Condition((instType == Bits(32)(2)) | (instType == Bits(32)(3))):
                            alu_arr[j].instId.push(self.inst[i])
                            alu_arr[j].lhs.push(self.vj[i])
                            alu_arr[j].rhs.push(self.A[i])
                            alu_arr[j].newId.push(self.dest[i])
                        # type B
                        with Condition(instType == Bits(32)(5)):
                            alu_arr[j].instId.push(self.inst[i])
                            alu_arr[j].lhs.push(self.vj[i])
                            alu_arr[j].rhs.push(self.vk[i])
                            alu_arr[j].newId.push(self.dest[i])
                        # type U (auipc/lui rd label)
                        with Condition(instType == Bits(32)(6)):
                            alu_arr[j].instId.push(self.inst[i])
                            alu_arr[j].lhs.push(self.vj[i])
                            alu_arr[j].rhs.push(self.vk[i])
                            alu_arr[j].newId.push(self.dest[i])
                        self.clear(i)
                    hasForward = hasForward | ((count == totalPrevious) & (~alu_arr[j].busy[0]) & canExecute)
                totalPrevious = totalPrevious + hasForward.bitcast(Bits(32))

            # forward into agu & lsb
            tag = Bits(1)(1)
            for i in range(self.rsSize):
                canExecute = self.busy[i] & (self.qj[i] == Bits(32)(0)) & (self.qk[i] == Bits(32)(0)) & (
                        self.inst[i] >= Bits(32)(20)) & (Bits(32)(27) >= self.inst[i])
                with Condition(tag & canExecute):
                    agu.lhs.push(self.vj[i])
                    agu.rhs.push(self.A[i])
                    agu.newId.push(self.dest[i])
                    lsb.newId_rs.push(self.dest[i])
                    lsb.wdata.push(self.vk[i])
                    self.clear(i)
                tag = tag & (~canExecute)

        for i in range(8):
            alu_arr[i].async_called()
        agu.async_called()
        # self.log()

    def log(self):
        log('-'*50)
        for i in range(self.rsSize):
            log('busy:{} op:{} vj:{} vk:{} qj:{} qk:{} dest:{} A:{}', self.busy[i], self.inst[i],
                self.vj[i], self.vk[i], self.qj[i], self.qk[i], self.dest[i],
                self.A[i])
        log('-'*50)

    def clear(self,ind):
        self.busy[ind] = Bits(1)(0)
        self.inst[ind] = Bits(32)(0)
        self.vj[ind] = Bits(32)(0)
        self.vk[ind] = Bits(32)(0)
        self.qj[ind] = Bits(32)(0)
        self.qk[ind] = Bits(32)(0)
        self.dest[ind] = Bits(32)(0)
        self.A[ind] = Bits(32)(0)

    def full(self):
        cnt = Bits(32)(0)
        for i in range(self.rsSize):
            cnt = cnt + (~self.busy[i]).bitcast(Bits(32))
        return Bits(32)(2) >= cnt
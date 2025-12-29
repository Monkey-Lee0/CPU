from assassyn.frontend import *

class RegFile(Downstream):
    def __init__(self):
        self.Regs = RegArray(
            scalar_ty=Bits(32),
            size=32,
        )
        super().__init__()

    @downstream.combinational
    def build(self,isRead = Bits(1)(0),isWrite = Bits(1)(0),ReadIndex = Bits(32)(0)
              ,WriteIndex = Bits(32)(0),WriteValue = Bits(32)(32)):
        res = Bits(32)(0)
        logRegs(self.Regs)
        res = isRead.select(ReadRegs(self.Regs, ReadIndex),res)
        res = isWrite.select(WriteRegs(self.Regs,isWrite, WriteIndex, WriteValue),res)
        return res

def logRegs(RF):
    for i in range(32):
        log("Reg[{}] {}", Bits(32)(i), RF[Bits(32)(i)])

def ReadRegs(RF,ind):
    res = (ind < Bits(32)(32)).select(RF[ind],Bits(32)(0))
    return res

def WriteRegs(RF,isWrite,ind,WV):
    RF[ind] = isWrite.select(WV,RF[ind])
    return Bits(32)(0)

class BusyFile(Downstream):
    def __init__(self):
        self.Valids = RegArray(
            scalar_ty=Bits(1),
            size=32,
        )
        super().__init__()

    @downstream.combinational
    def build(self,isRead = Bits(1)(0),isWrite = Bits(1)(0),ReadIndex = Bits(32)(0)
              ,WriteIndex = Bits(32)(0),WriteValue = Bits(1)(0)):
        res = Bits(1)(0)
        logValids(self.Valids)
        res = isRead.select(ReadValids(self.Valids, ReadIndex),res)
        res = isWrite.select(WriteValids(self.Valids,isWrite, WriteIndex, WriteValue),res)
        return res

def logValids(VF):
    for i in range(32):
        log("Valid[{}] {}", Bits(32)(i), VF[Bits(32)(i)])

def ReadValids(VF,ind):
    res = (ind < Bits(32)(32)).select(VF[ind],Bits(1)(0))
    return res

def WriteValids(VF,isWrite,ind,WV):
    VF[ind] = isWrite.select(WV,VF[ind])
    return Bits(1)(0)

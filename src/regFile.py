from assassyn.frontend import *

class RegFile(Downstream):
    def __init__(self):
        self.Regs=RegArray(Bits(32), 32)
        super().__init__()

    # If you want to write, please leisurely use a variable
    # to get the meaningless False, make isWrite True and
    # respectively input WriteIndex and WriteValue.
    # If you want to read Regs, please use a variable to get the
    # Bits(32) Value, make isRead True and input ReadIndex

    def build(self,isRead=False,isWrite=False,ReadIndex=0,
              WriteIndex=0,WriteValue=Bits(32)(0)):
        res = Bits(32)(0)
        res = isRead.select(ReadRegs(self.Regs,ReadIndex),res)
        res = isWrite.select(WriteRegs(self.Regs,WriteIndex,WriteValue),res)
        return res

def ReadRegs(RF,ind):
    return RF[ind]

def WriteRegs(RF,ind,WV):
    RF[ind] = WV
    return RF[ind]


class ValidFile(Downstream):
    def __init__(self):
        self.Valid=RegArray(Bits(1), 32)
        super().__init__()

    # If you want to read Validations, please use a variable to get the
    # Bits(1) Value, make isValid True and input ValidIndex
    # If you want to write Validation, please leisurely use a variable to get the
    # Bits(1) Value. You can select two pattern of setting occupied or setting valid

    def build(self,isRead=False,ReadIndex=0,isOccupy=False,OccupyIndex=0,
            isValidate=False,ValidateIndex=0):
        res = Bits(1)(0)
        res = isRead.select(Valid_Read(self.Valid,ReadIndex),res)
        res = isValidate.select(Validate_Regs(self.Valid,ValidateIndex),res)
        res = isOccupy.select(Occupy_Regs(self.Valid,OccupyIndex),res)
        return res

def Valid_Read(VF,ind):
    return VF[ind]

def Validate_Regs(VF,ind):
    VF[ind] = Bits(1)(1)
    return VF[ind]

def Occupy_Regs(VF,ind):
    VF[ind] = Bits(1)(0)
    return VF[ind]
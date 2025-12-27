from assassyn.frontend import *
from instruction import *

def takeBitsRange(b:Bits, l:int, r:int):
    return (b>>Bits(32)(l))&((Bits(32)(1)<<Bits(32)(r-l+1))-Bits(32)(1))

def parseInst(inst:Bits):
    opcode = takeBitsRange(inst, 0, 6)
    instType = opcode.case({
        Bits(32)(0b0110011):Bits(32)(1),
        Bits(32)(0b0010011):Bits(32)(2),
        Bits(32)(0b0000011):Bits(32)(2),
        Bits(32)(0b0100011):Bits(32)(3),
        Bits(32)(0b1100011):Bits(32)(4),
        Bits(32)(0b1101111):Bits(32)(5),
        Bits(32)(0b1100111):Bits(32)(2),
        Bits(32)(0b0010111):Bits(32)(6),
        None:Bits(32)(0)
    })

    with Condition(instType == Bits(32)(1)):
        parseRInst(inst).print()


def parseRInst(inst: Bits):
    funct3 = takeBitsRange(inst, 12, 14)
    funct7 = takeBitsRange(inst, 25, 31)
    rd = takeBitsRange(inst, 7, 11)
    rs1 = takeBitsRange(inst, 15, 19)
    rs2 = takeBitsRange(inst, 20, 24)
    instId = Bits(32)(0)

    combinedVal = (funct3 << Bits(32)(7)) | funct7
    for [expect, current] in RInst.items():
        instId = (combinedVal == expect).select(current, instId)

    return Instruction(Bits(32)(1), instId, rd, rs1, rs2, Bits(32)(0))
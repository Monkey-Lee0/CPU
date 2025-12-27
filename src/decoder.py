from inst import *

def takeBitsRange(b:Bits, l:int, r:int):
    return (b>>Bits(32)(l))&((Bits(32)(1)<<Bits(32)(r-l+1))-Bits(32)(1))

def parseInst(inst:Bits):
    opcode = takeBitsRange(inst, 0, 6)
    res = Inst(Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0))

    res.checkCopy(opcode == Bits(32)(0b0110011), parseRInst(inst))
    res.checkCopy(opcode == Bits(32)(0b0010011) or opcode == Bits(32)(0b0000011) or opcode == Bits(32)(0b1100111),
                parseIInst(inst))
    # with Condition(opcode == Bits(32)(0b0100011)):
    #     res = parseSInst(inst)
    # with Condition(opcode == Bits(32)(0b0100011)):
    #     res = parseBInst(inst)
    # with Condition(opcode == Bits(32)(0b1101111)):
    #     res = parseJInst(inst)
    # with Condition(opcode == Bits(32)(0b0010111)):
    #     res = parseUInst(inst)
    res.print()
    return res


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

    return Inst(Bits(32)(1), instId, rd, rs1, rs2, Bits(32)(0))


def parseIInst(inst: Bits):
    opcode = takeBitsRange(inst, 0 ,6)
    funct3 = takeBitsRange(inst, 12, 14)
    isStar = (opcode == Bits(32)(0b0010011)) and (funct3 == Bits(32)(0b001) or funct3 == Bits(32)(0b101))

    rd = takeBitsRange(inst, 7, 11)
    rs1 = takeBitsRange(inst, 15, 19)
    imm = takeBitsRange(inst, 20, 31)
    instId = Bits(32)(0)

    combinedVal = (opcode << Bits(32)(3)) | funct3
    for [expect, current] in IInst.items():
        instId = (combinedVal == expect).select(current, instId)

    return Inst(Bits(32)(2), instId, rd, rs1, Bits(32)(0), imm).checkCopy(isStar, parseIStarInst(inst))


def parseIStarInst(inst: Bits):
    return Inst(Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0))
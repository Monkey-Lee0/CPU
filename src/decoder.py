from assassyn.ir.module.downstream import combinational

from inst import *

def takeBitsRange(b:Bits, l:int, r:int):
    return (b>>Bits(32)(l))&((Bits(32)(1)<<Bits(32)(r-l+1))-Bits(32)(1))

def mergeBits(b:Bits, rule:dict):
    res = Bits(32)(0)
    for fr, to in rule.items():
        res = res | (takeBitsRange(b, fr[0], fr[1]) << Bits(32)(to[0]))
    return res

def parseInst(inst:Bits):
    opcode = takeBitsRange(inst, 0, 6)
    res = Inst(Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0))

    res.checkCopy(opcode == Bits(32)(0b0110011), parseRInst(inst))
    res.checkCopy(opcode == Bits(32)(0b0010011) or opcode == Bits(32)(0b0000011) or opcode == Bits(32)(0b1100111),
                parseIInst(inst))
    res.checkCopy(opcode == Bits(32)(0b0100011), parseSInst(inst))
    res.checkCopy(opcode == Bits(32)(0b1100011), parseBInst(inst))
    res.checkCopy(opcode == Bits(32)(0b0010111) or opcode == Bits(32)(0b0110111)), parseUInst(inst)
    res.checkCopy(opcode == Bits(32)(0b1101111), parseJInst(inst))
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
    funct3 = takeBitsRange(inst, 12, 14)
    rd = takeBitsRange(inst, 7, 11)
    rs1 = takeBitsRange(inst, 15, 19)
    imm = takeBitsRange(inst, 20, 24)
    funct7 = takeBitsRange(inst, 25, 31)
    instId = Bits(32)(0)

    combinedVal = (funct3 << Bits(32)(7)) | funct7
    for [expect, current] in IInst.items():
        instId = (combinedVal == expect).select(current, instId)

    return Inst(Bits(32)(3), instId, rd, rs1, Bits(32)(0), imm)

def parseSInst(inst: Bits):
    funct3 = takeBitsRange(inst, 12, 14)
    rs1 = takeBitsRange(inst, 15, 19)
    rs2 = takeBitsRange(inst, 20, 24)
    imm = mergeBits(inst, {
        (7,11):(0,4),
        (25,31):(5,11)
    })
    instId = Bits(32)(0)

    for [expect, current] in SInst.items():
        instId = (funct3 == expect).select(current, instId)

    return Inst(Bits(32)(4), instId, Bits(32)(0), rs1, rs2, imm)

def parseBInst(inst: Bits):
    funct3 = takeBitsRange(inst, 12, 14)
    rs1 = takeBitsRange(inst, 15, 19)
    rs2 = takeBitsRange(inst, 20, 24)
    imm = mergeBits(inst, {
        (8,11):(1,4),
        (25,30):(5,10),
        (31,31):(12,12),
        (7,7):(11,11)
    })
    instId = Bits(32)(0)

    for [expect, current] in BInst.items():
        instId = (funct3 == expect).select(current, instId)

    return Inst(Bits(32)(5), instId, Bits(32)(0), rs1, rs2, imm)

def parseUInst(inst: Bits):
    opcode = takeBitsRange(inst, 0, 6)
    rd = takeBitsRange(inst, 7, 11)
    imm = mergeBits(inst, {
        (12,31):(12,31)
    })
    instId = Bits(32)(0)

    for [expect, current] in UInst.items():
        instId = (opcode == expect).select(current, instId)

    return Inst(Bits(32)(6), instId, rd, Bits(32)(0), Bits(32)(0), imm)

def parseJInst(inst: Bits):
    opcode = takeBitsRange(inst, 0, 6)
    rd = takeBitsRange(inst, 7, 11)
    imm = mergeBits(inst, {
        (12, 19):(12, 19),
        (20, 20):(11, 11),
        (21, 30):(1, 10),
        (31, 31):(12, 12),
    })
    instId = Bits(32)(0)

    for [expect, current] in JInst.items():
        instId = (opcode == expect).select(current, instId)

        return Inst(Bits(32)(7),instId, rd, Bits(32)(0), Bits(32)(0), imm)

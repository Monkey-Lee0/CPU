from assassyn.ir.module.downstream import combinational

from inst import *
from utils import bitsToInt32

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
    res.checkCopy((opcode == Bits(32)(0b0010011)) | (opcode == Bits(32)(0b0000011)) | (opcode == Bits(32)(0b1100111)),
                parseIInst(inst))
    res.checkCopy(opcode == Bits(32)(0b0100011), parseSInst(inst))
    res.checkCopy(opcode == Bits(32)(0b1100011), parseBInst(inst))
    res.checkCopy((opcode == Bits(32)(0b0010111)) | (opcode == Bits(32)(0b0110111)), parseUInst(inst))
    res.checkCopy(opcode == Bits(32)(0b1101111), parseJInst(inst))
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
    isStar = (opcode == Bits(32)(0b0010011)) & ((funct3 == Bits(32)(0b001)) | ((funct3 == Bits(32)(0b101))))

    rd = takeBitsRange(inst, 7, 11)
    rs1 = takeBitsRange(inst, 15, 19)
    imm = takeBitsRange(inst, 20, 31)
    instId = Bits(32)(0)

    combinedVal = (opcode << Bits(32)(3)) | funct3
    for [expect, current] in IInst.items():
        instId = (combinedVal == expect).select(current, instId)

    return Inst(Bits(32)(2), instId, rd, rs1, Bits(32)(0), bitsToInt32(imm, 12).bitcast(Bits(32))).checkCopy(isStar, parseIStarInst(inst))


def parseIStarInst(inst: Bits):
    funct3 = takeBitsRange(inst, 12, 14)
    rd = takeBitsRange(inst, 7, 11)
    rs1 = takeBitsRange(inst, 15, 19)
    imm = takeBitsRange(inst, 20, 24)
    funct7 = takeBitsRange(inst, 25, 31)
    instId = Bits(32)(0)

    combinedVal = (funct3 << Bits(32)(7)) | funct7
    for [expect, current] in IStarInst.items():
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

    return Inst(Bits(32)(4), instId, Bits(32)(0), rs1, rs2, bitsToInt32(imm, 12).bitcast(Bits(32)))

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

    return Inst(Bits(32)(5), instId, Bits(32)(0), rs1, rs2, bitsToInt32(imm, 13).bitcast(Bits(32)))

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
        (31, 31):(20, 20),
    })
    instId = Bits(32)(0)

    for [expect, current] in JInst.items():
        instId = (opcode == expect).select(current, instId)

    return Inst(Bits(32)(7),instId, rd, Bits(32)(0), Bits(32)(0), bitsToInt32(imm, 21).bitcast(Bits(32)))

def parseCInst(inst: Bits):
    opcode = takeBitsRange(inst, 0, 1)
    res = Inst(Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0))

    res.checkCopy(opcode == Bits(32)(0b00), parseC0Inst(inst))
    res.checkCopy(opcode == Bits(32)(0b01), parseC1Inst(inst))
    res.checkCopy(opcode == Bits(32)(0b10), parseC2Inst(inst))
    return res

def parseC0Inst(inst: Bits):
    funct3 = takeBitsRange(inst, 13, 15)
    res = Inst(Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0))
    res = res.checkCopy(funct3 == Bits(32)(0b010), parseClw(inst))
    res = res.checkCopy(funct3 == Bits(32)(0b110), parseCsw(inst))
    res = res.checkCopy(funct3 == Bits(32)(0b000), parseCaddi4spn(inst))
    return res

def parseClw(inst: Bits):
    rs1 = takeBitsRange(inst, 7, 9)
    rd = takeBitsRange(inst, 2, 4)
    imm = mergeBits(inst, {
        (6, 6):(2, 2),
        (10, 12):(3, 5),
        (5, 5):(6, 6)
    }) # zero-extend
    return Inst(Bits(32)(2), Bits(32)(24), rd, rs1, Bits(32)(0), imm)

def parseCsw(inst: Bits):
    rs1 = takeBitsRange(inst, 7, 9)
    rs2 = takeBitsRange(inst, 2, 4)
    imm = mergeBits(inst, {
        (6, 6): (2, 2),
        (10, 12): (3, 5),
        (5, 5): (6, 6)
    }) # zero-extend
    return Inst(Bits(32)(5), Bits(32)(27), Bits(32)(0), rs1, rs2, imm)

def parseCaddi4spn(inst: Bits):
    sp = Bits(32)(2)
    rd = takeBitsRange(inst, 2, 4)
    imm = mergeBits(inst, {
        (5, 5):(3, 3),
        (6, 6):(2, 2),
        (7, 10):(6, 9),
        (11, 12):(4, 5),
    }) # zero-extend
    return Inst(Bits(32)(2), Bits(32)(24), rd, sp, Bits(32)(0), imm)

def parseC1Inst(inst: Bits):
    funct3 = takeBitsRange(inst, 13, 15)
    res = Inst(Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0))
    res = res.checkCopy(funct3 == Bits(32)(0b101), parseCj(inst))
    res = res.checkCopy(funct3 == Bits(32)(0b001), parseCjal(inst))
    res = res.checkCopy(funct3 == Bits(32)(0b110), parseCbeqz(inst))
    res = res.checkCopy(funct3 == Bits(32)(0b111), parseCbnez(inst))
    res = res.checkCopy(funct3 == Bits(32)(0b010), parseCli(inst))
    res = res.checkCopy(funct3 == Bits(32)(0b011), parseClui(inst))
    res = res.checkCopy(funct3 == Bits(32)(0b000), parseCaddi(inst))
    res = res.checkCopy(funct3 == Bits(32)(0b011), parseCaddi16sp(inst))
    res = res.checkCopy(funct3 == Bits(32)(0b100), parseCBS(inst))
    return res

def parseCj(inst: Bits):
    zero = Bits(32)(0)
    imm = mergeBits(inst, {
        (2, 2):(5, 5),
        (3, 5):(1, 3),
        (6, 6):(7, 7),
        (7, 7):(6, 6),
        (8, 8):(10, 10),
        (9, 10):(8, 9),
        (11, 11):(4, 4),
        (12, 12):(11, 11)
    }) # zero-extend
    return Inst(Bits(32)(7), Bits(32)(34), zero, Bits(32)(0), Bits(32)(0), bitsToInt32(imm, 12).bitcast(Bits(32)))

def parseCjal(inst: Bits):
    ra = Bits(32)(1)
    imm = mergeBits(inst, {
        (2, 2): (5, 5),
        (3, 5): (1, 3),
        (6, 6): (7, 7),
        (7, 7): (6, 6),
        (8, 8): (10, 10),
        (9, 10): (8, 9),
        (11, 11): (4, 4),
        (12, 12): (11, 11)
    }) # sign-extend
    return Inst(Bits(32)(7), Bits(32)(34), ra, Bits(32)(0), Bits(32)(0), bitsToInt32(imm, 12).bitcast(Bits(32)))

def parseCbeqz(inst: Bits):
    zero = Bits(32)(0)
    rs1 = takeBitsRange(inst, 7, 9)
    imm = mergeBits(inst, {
        (2, 2): (5, 5),
        (3, 4): (1, 2),
        (5, 6): (6, 7),
        (10, 11): (3, 4),
        (12, 12): (8, 8)
    }) # sign-extend
    return Inst(Bits(32)(5), Bits(32)(28), Bits(32)(0), rs1, zero, bitsToInt32(imm, 9).bitcast(Bits(32)))

def parseCbnez(inst: Bits):
    zero = Bits(32)(0)
    rs1 = takeBitsRange(inst, 7, 9)
    imm = mergeBits(inst, {
        (2, 2): (5, 5),
        (3, 4): (1, 2),
        (5, 6): (6, 7),
        (10, 11): (3, 4),
        (12, 12): (8, 8)
    })  # sign-extend
    return Inst(Bits(32)(5), Bits(32)(33), Bits(32)(0), rs1, zero, bitsToInt32(imm, 9).bitcast(Bits(32)))

def parseCli(inst: Bits):
    zero = Bits(32)(0)
    rd = takeBitsRange(inst, 7, 11)
    imm = mergeBits(inst, {
        (2, 6):(0, 4),
        (12, 12):(5, 5)
    }) # sign-extend
    return Inst(Bits(32)(2), Bits(32)(11), rd, zero, Bits(32)(0), bitsToInt32(imm, 6).bitcast(Bits(32)))

def parseClui(inst: Bits):
    rd = takeBitsRange(inst, 7, 11)
    imm = mergeBits(inst, {
        (2, 6):(12, 16),
        (12, 12):(17, 17)
    }) # zero-extend
    return Inst(Bits(32)(6), Bits(32)(37), rd, Bits(32)(0), Bits(32)(0), imm)

def parseCaddi(inst: Bits):
    rd = takeBitsRange(inst, 7, 11)
    imm = mergeBits(inst, {
        (2, 6): (0, 4),
        (12, 12): (5, 5)
    }) # sign-extend
    return Inst(Bits(32)(2), Bits(32)(11), rd, rd, Bits(32)(0), bitsToInt32(imm, 6).bitcast(Bits(32)))

def parseCaddi16sp(inst: Bits):
    sp = Bits(32)(2)
    imm = mergeBits(inst, {
        (2, 2): (5, 5),
        (3, 4): (7, 8),
        (5, 5): (6, 6),
        (6, 6): (4, 4),
        (12, 12): (9, 9),
    }) # sign-extend
    return Inst(Bits(32)(2), Bits(32)(11), sp, sp, Bits(32)(0), bitsToInt32(imm, 10).bitcast(Bits(32)))

def parseCBS(inst: Bits):
    funct2 = takeBitsRange(inst, 10, 11)
    res = Inst(Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0))
    res = res.checkCopy(funct2 == Bits(32)(0b00), parseCsrli(inst))
    res = res.checkCopy(funct2 == Bits(32)(0b01), parseCsrai(inst))
    res = res.checkCopy(funct2 == Bits(32)(0b10), parseCandi(inst))
    res = res.checkCopy(funct2 == Bits(32)(0b11), parseCS(inst))
    return res

def parseCsrli(inst: Bits):
    rd = takeBitsRange(inst, 7, 9)
    imm = mergeBits(inst, {
        (2, 6):(0, 4),
        (12, 12): (5, 5),
    }) # zero-extend
    return Inst(Bits(32)(3), Bits(32)(16), rd, rd, Bits(32)(0), imm)

def parseCsrai(inst: Bits):
    rd = takeBitsRange(inst, 7, 9)
    imm = mergeBits(inst, {
        (2, 6): (0, 4),
        (12, 12): (5, 5),
    })  # zero-extend
    return Inst(Bits(32)(3), Bits(32)(17), rd, rd, Bits(32)(0), imm)

def parseCandi(inst: Bits):
    rd = takeBitsRange(inst, 7, 9)
    imm = mergeBits(inst, {
        (2, 6): (0, 4),
        (12, 12): (5, 5),
    })  # zero-extend
    return Inst(Bits(32)(2), Bits(32)(12), rd, rd, Bits(32)(0), bitsToInt32(imm, 6).bitcast(Bits(32)))

def parseCS(inst: Bits):
    funct2 = takeBitsRange(inst, 8,  9)
    res = Inst(Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0))
    res = res.checkCopy(funct2 == Bits(32)(0b00), parseCand(inst))
    res = res.checkCopy(funct2 == Bits(32)(0b01), parseCor(inst))
    res = res.checkCopy(funct2 == Bits(32)(0b10), parseCxor(inst))
    res = res.checkCopy(funct2 == Bits(32)(0b11), parseCsub(inst))
    return res

def parseCand(inst: Bits):
    rd = takeBitsRange(inst, 7, 9)
    rs2 = takeBitsRange(inst, 2, 4)
    return Inst(Bits(32)(1), Bits(32)(3), rd, rd, rs2, Bits(32)(0))

def parseCor(inst: Bits):
    rd = takeBitsRange(inst, 7, 9)
    rs2 = takeBitsRange(inst, 2, 4)
    return Inst(Bits(32)(1), Bits(32)(4), rd, rd, rs2, Bits(32)(0))

def parseCxor(inst: Bits):
    rd = takeBitsRange(inst, 7, 9)
    rs2 = takeBitsRange(inst, 2, 4)
    return Inst(Bits(32)(1), Bits(32)(5), rd, rd, rs2, Bits(32)(0))

def parseCsub(inst: Bits):
    rd = takeBitsRange(inst, 7, 9)
    rs2 = takeBitsRange(inst, 2, 4)
    return Inst(Bits(32)(1), Bits(32)(2), rd, rd, rs2, Bits(32)(0))

def parseC2Inst(inst: Bits):
    funct3 = takeBitsRange(inst, 13, 15)
    res = Inst(Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0))
    res = res.checkCopy(funct3 == Bits(32)(0b010), parseClwsp(inst))
    res = res.checkCopy(funct3 == Bits(32)(0b110), parseCswsp(inst))
    res = res.checkCopy(funct3 == Bits(32)(0b100), parseCR(inst))
    res = res.checkCopy(funct3 == Bits(32)(0b000), parseCslli(inst))
    return res

def parseClwsp(inst: Bits):
    sp = Bits(32)(2)
    rd = takeBitsRange(inst, 7, 11)
    imm = mergeBits(inst, {
        (2, 3):(6, 7),
        (4, 6): (2, 4),
        (12, 12): (5, 5),
    }) # zero-extend
    return Inst(Bits(32)(2), Bits(32)(24), rd, sp, Bits(32)(0), imm)

def parseCswsp(inst: Bits):
    sp = Bits(32)(2)
    rs2 = takeBitsRange(inst, 2, 6)
    imm = mergeBits(inst, {
        (7, 8): (6, 7),
        (9, 12): (2, 5),
    })
    return Inst(Bits(32)(5), Bits(32)(27), Bits(32)(0), sp, rs2, imm)

def parseCR(inst: Bits):
    funct1 = takeBitsRange(inst, 12,  12)
    res = Inst(Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0), Bits(32)(0))
    res = res.checkCopy(funct1 == Bits(32)(0b0), parseCmv(inst))
    res = res.checkCopy(funct1 == Bits(32)(0b1), parseCadd(inst))
    return res

def parseCmv(inst: Bits):
    zero = Bits(32)(0)
    rd = takeBitsRange(inst, 2, 5)
    rs2 = takeBitsRange(inst, 6, 9)
    return Inst(Bits(32)(1), Bits(32)(1), rd, zero, rs2, Bits(32)(0))

def parseCadd(inst: Bits):
    rd = takeBitsRange(inst, 2, 5)
    rs2 = takeBitsRange(inst, 6, 9)
    return Inst(Bits(32)(1), Bits(32)(1), rd, rd, rs2, Bits(32)(0))

def parseCslli(inst: Bits):
    rd = takeBitsRange(inst, 7, 11)
    imm = mergeBits(inst, {
        (2, 6): (0, 4),
        (12, 12): (5, 5),
    })
    return Inst(Bits(32)(3), Bits(32)(15), rd, rd, Bits(32)(0), imm)
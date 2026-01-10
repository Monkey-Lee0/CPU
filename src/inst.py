from assassyn.frontend import *

def bitsToInt(b, bit1, bit2):
    mxVal = Bits(32)(1) << Bits(32)(bit1-1)
    bInt = b.bitcast(Int(bit2))
    return (b < mxVal).select(bInt, bInt - mxVal - mxVal)

class Inst:

    type: Bits
    id: Bits
    rd: Bits
    rs1: Bits
    rs2: Bits
    imm: Bits

    def __init__(self, _type, _id, _rd, _rs1, _rs2, _imm):
        self.type = _type
        self.id = _id
        self.rd = _rd
        self.rs1 = _rs1
        self.rs2 = _rs2
        self.imm = _imm

    def checkCopy(self, cond, other):
        self.type = cond.select(other.type, self.type)
        self.id = cond.select(other.id, self.id)
        self.rd = cond.select(other.rd, self.rd)
        self.rs1 = cond.select(other.rs1, self.rs1)
        self.rs2 = cond.select(other.rs2, self.rs2)
        self.imm = cond.select(other.imm, self.imm)
        return self

    def print(self):
        with Condition(self.type == Bits(32)(0)):
            log('illegal')
        with Condition(self.type == Bits(32)(1)): # type R
            log('%{} ${} ${} ${}', self.id, self.rd, self.rs1, self.rs2)
        with Condition(self.type == Bits(32)(2)): # type I
            log('%{} ${} ${} {}', self.id, self.rd, self.rs1, self.imm)
        with Condition(self.type == Bits(32)(3)):
            log('%{} ${} ${} {}', self.id, self.rd, self.rs1, self.imm)
        with Condition(self.type == Bits(32)(4)):
            log('%{} ${} {}(${})', self.id, self.rs2, self.imm, self.rs1)
        with Condition(self.type == Bits(32)(5)):
            log('%{} ${} ${} {}', self.id, self.rs1, self.rs2, bitsToInt(self.imm, 13, 32))
        with Condition(self.type == Bits(32)(6)):
            log('%{} ${} {}', self.id, self.rd, self.imm)
        with Condition(self.type == Bits(32)(7)):
            log('%{} ${} {}', self.id, self.rd, self.imm)

RInst = { # funct3 - funct7 -> id
    Bits(32)(0b0000000000):Bits(32)(1), # add
    Bits(32)(0b0000100000):Bits(32)(2), # sub
    Bits(32)(0b1110000000):Bits(32)(3), # and
    Bits(32)(0b1100000000):Bits(32)(4), # or
    Bits(32)(0b1000000000):Bits(32)(5), # xor
    Bits(32)(0b0010000000):Bits(32)(6), # sll
    Bits(32)(0b1010000000):Bits(32)(7), # srl
    Bits(32)(0b1010100000):Bits(32)(8), # sra
    Bits(32)(0b0100000000):Bits(32)(9), # slt
    Bits(32)(0b0110000000):Bits(32)(10), # sltu
}

IInst = { # opcode - funct3 -> id
    Bits(32)(0b0010011000):Bits(32)(11), # addi
    Bits(32)(0b0010011111):Bits(32)(12), # andi
    Bits(32)(0b0010011110):Bits(32)(13), # ori
    Bits(32)(0b0010011100):Bits(32)(14), # xori
    Bits(32)(0b0010011010):Bits(32)(18), # slti
    Bits(32)(0b0010011011):Bits(32)(19), # sltiu
    Bits(32)(0b0000011000):Bits(32)(20), # lb
    Bits(32)(0b0000011100):Bits(32)(21), # lbu
    Bits(32)(0b0000011001):Bits(32)(22), # lh
    Bits(32)(0b0000011101):Bits(32)(23), # lhu
    Bits(32)(0b0000011010):Bits(32)(24), # lw
    Bits(32)(0b1100111000):Bits(32)(35), # jalr
}

IStarInst = { # funct3 - funct7 -> id
    Bits(32)(0b0010000000):Bits(32)(15),
    Bits(32)(0b1010000000):Bits(32)(16),
    Bits(32)(0b1010100000):Bits(32)(17),
}

SInst = { # funct3 -> id
    Bits(32)(0b000):Bits(32)(25),
    Bits(32)(0b001):Bits(32)(26),
    Bits(32)(0b010):Bits(32)(27),
}

BInst = { # funct3 -> id
    Bits(32)(0b000):Bits(32)(28),
    Bits(32)(0b101):Bits(32)(29),
    Bits(32)(0b111):Bits(32)(30),
    Bits(32)(0b100):Bits(32)(31),
    Bits(32)(0b110):Bits(32)(32),
    Bits(32)(0b001):Bits(32)(33),
}

UInst = {
    Bits(32)(0b0010111):Bits(32)(36),
    Bits(32)(0b0110111):Bits(32)(37),
}

JInst = {
    Bits(32)(0b1101111):Bits(32)(34),
}

InstName = [
    'illegal',
    'add',
    'sub',
    'and',
    'or',
    'xor',
    'sll',
    'srl',
    'sra',
    'slt',
    'sltu',
    'addi',
    'andi',
    'ori',
    'xori',
    'slli',
    'srli',
    'srai',
    'slti',
    'sltiu',
    'lb',
    'lbu',
    'lh',
    'lhu',
    'lw',
    'sb',
    'sh',
    'sw',
    'beq',
    'bge',
    'bgeu',
    'blt',
    'bltu',
    'bne',
    'jal',
    'jalr',
    'auipc',
    'lui'
]

RegName = [
    'zero',
    'ra',
    'sp',
    'gp',
    'tp',
    't0',
    't1',
    't2',
    's0',
    's1',
    'a0',
    'a1',
    'a2',
    'a3',
    'a4',
    'a5',
    'a6',
    'a7',
    's2',
    's3',
    's4',
    's5',
    's6',
    's7',
    's8',
    's9',
    's10',
    's11',
    't3',
    't4',
    't5',
    't6'
]

idToTypeDict = {
    Bits(32)(0):Bits(32)(0),
    Bits(32)(1):Bits(32)(1),
    Bits(32)(2):Bits(32)(1),
    Bits(32)(3):Bits(32)(1),
    Bits(32)(4):Bits(32)(1),
    Bits(32)(5):Bits(32)(1),
    Bits(32)(6):Bits(32)(1),
    Bits(32)(7):Bits(32)(1),
    Bits(32)(8):Bits(32)(1),
    Bits(32)(9):Bits(32)(1),
    Bits(32)(10):Bits(32)(1),
    Bits(32)(11):Bits(32)(2),
    Bits(32)(12):Bits(32)(2),
    Bits(32)(13):Bits(32)(2),
    Bits(32)(14):Bits(32)(2),
    Bits(32)(15):Bits(32)(3),
    Bits(32)(16):Bits(32)(3),
    Bits(32)(17):Bits(32)(3),
    Bits(32)(18):Bits(32)(2),
    Bits(32)(19):Bits(32)(2),
    Bits(32)(20):Bits(32)(2),
    Bits(32)(21):Bits(32)(2),
    Bits(32)(22):Bits(32)(2),
    Bits(32)(23):Bits(32)(2),
    Bits(32)(24):Bits(32)(2),
    Bits(32)(25):Bits(32)(4),
    Bits(32)(26):Bits(32)(4),
    Bits(32)(27):Bits(32)(4),
    Bits(32)(28):Bits(32)(5),
    Bits(32)(29):Bits(32)(5),
    Bits(32)(30):Bits(32)(5),
    Bits(32)(31):Bits(32)(5),
    Bits(32)(32):Bits(32)(5),
    Bits(32)(33):Bits(32)(5),
    Bits(32)(34):Bits(32)(7),
    Bits(32)(35):Bits(32)(2),
    Bits(32)(36):Bits(32)(6),
    Bits(32)(37):Bits(32)(6),
}

def idToType(instId):
    res = Bits(32)(0)
    for Id, Type in idToTypeDict.items():
        res = (Id == instId).select(Type, res)
    return res

def isMemoryInst(instId):
    return (instId >= Bits(32)(20)) & (Bits(32)(27) >= instId)
from assassyn.frontend import *
from utils import bitsToInt32

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
            log('%{} ${} ${} {}', self.id, self.rs1, self.rs2, self.imm.bitcast(Int(32)))
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
    Bits(32)(0b0000000001):Bits(32)(38), # mul
    Bits(32)(0b0010000001):Bits(32)(39), # mulh
    Bits(32)(0b0100000001):Bits(32)(40), # mulhsu
    Bits(32)(0b0110000001):Bits(32)(41), # mulhu
    Bits(32)(0b1000000001):Bits(32)(42), # div
    Bits(32)(0b1010000001):Bits(32)(43), # divu
    Bits(32)(0b1100000001):Bits(32)(44), # rem
    Bits(32)(0b1110000001):Bits(32)(45), # remu
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
    'illegal', # 0
    'add', # 1
    'sub', # 2
    'and', # 3
    'or', # 4
    'xor', # 5
    'sll', # 6
    'srl', # 7
    'sra', # 8
    'slt', # 9
    'sltu', # 10
    'addi', # 11
    'andi', # 12
    'ori', # 13
    'xori', # 14
    'slli', # 15
    'srli', # 16
    'srai', # 17
    'slti', # 18
    'sltiu', # 19
    'lb', # 20
    'lbu', # 21
    'lh', # 22
    'lhu', # 23
    'lw', # 24
    'sb', # 25
    'sh', # 26
    'sw', # 27
    'beq', # 28
    'bge', # 29
    'bgeu', # 30
    'blt', # 31
    'bltu', # 32
    'bne', # 33
    'jal', # 34
    'jalr', # 35
    'auipc', # 36
    'lui', # 37
    'mul', # 38
    'mulh', # 39
    'mulsu', # 40
    'mulhu', # 41
    'div', # 42
    'divu', # 43
    'rem', # 44
    'remu', # 45
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


# 1-R 2-I 3-I* 4-S 5-B 6-U 7-J

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
    Bits(32)(38):Bits(32)(1),
    Bits(32)(39):Bits(32)(1),
    Bits(32)(40):Bits(32)(1),
    Bits(32)(41):Bits(32)(1),
    Bits(32)(42):Bits(32)(1),
    Bits(32)(43):Bits(32)(1),
    Bits(32)(44):Bits(32)(1),
    Bits(32)(45):Bits(32)(1),
}

def idToType(instId):
    res = Bits(32)(0)
    for Id, Type in idToTypeDict.items():
        res = (Id == instId).select(Type, res)
    return res

def isMemoryInst(instId):
    return (instId >= Bits(32)(20)) & (Bits(32)(27) >= instId)
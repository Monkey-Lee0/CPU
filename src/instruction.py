from assassyn.frontend import *

class Instruction:

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

    def print(self):
        with Condition(self.type == Bits(32)(1)): # type R
            printInst(self.id, '{} {} {}', self.rd, self.rs1, self.rs2)

RInst = {
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

InstName = {
    Bits(32)(1):'add',
    Bits(32)(2):'sub',
    Bits(32)(3):'and',
    Bits(32)(4):'or',
    Bits(32)(5):'xor',
    Bits(32)(6):'sll',
    Bits(32)(7):'srl',
    Bits(32)(8):'sra',
    Bits(32)(9):'slt',
    Bits(32)(10):'sltu',
    Bits(32)(11):'addi',
    Bits(32)(12):'andi',
    Bits(32)(13):'ori',
    Bits(32)(14):'xori',
    Bits(32)(15):'slli',
    Bits(32)(16):'srli',
    Bits(32)(17):'srai',
    Bits(32)(18):'slti',
    Bits(32)(19):'sltiu',
    Bits(32)(20):'lb',
    Bits(32)(21):'lbu',
    Bits(32)(22):'lh',
    Bits(32)(23):'lhu',
    Bits(32)(24):'lw',
    Bits(32)(25):'sb',
    Bits(32)(26):'sh',
    Bits(32)(27):'sw',
    Bits(32)(28):'beq',
    Bits(32)(29):'bge',
    Bits(32)(30):'bgeu',
    Bits(32)(31):'blt',
    Bits(32)(32):'bltu',
    Bits(32)(33):'bne',
    Bits(32)(34):'jal',
    Bits(32)(35):'jalr',
    Bits(32)(36):'auipc',
    Bits(32)(37):'lui'
}

def printInst(instId:Bits, format:str, *args):
    with Condition(instId == Bits(32)(0)):
        log('illegal')
    for expectId, name in InstName.items():
        with Condition(instId == expectId):
            log(name+' '+format, *args)
    pass
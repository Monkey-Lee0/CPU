from assassyn.frontend import *
from utils import ValArray

class RegFile:
    def __init__(self, rob):
        super().__init__()
        self.regs = ValArray(Bits(32), 32, rob)
        self.dependence = ValArray(Bits(32), 32, rob)

    def build(self, wPos, wData, wId):
        self.regs[wPos] = wData
        self.dependence[wPos] = wId

    def log(self):
        for i in range(32):
            log("{}->regs:{} id:{}", Bits(32)(i), self.regs[i], self.dependence[i])

    def clearDependency(self):
        for i in range(32):
            self.dependence[i] = Bits(32)(0)

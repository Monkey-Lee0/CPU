from assassyn.frontend import *

class Predictor(Module):
    def __init__(self):
        super().__init__(ports={
            'resFromALU':Port(Bits(32)),
            'pc':Port(Bits(32)),
            'FlushInfo':Port(Bits(1))

        })

    def build(self,rob):
        pc = self.pc.pop()
        resFromALU = self.resFromALU.pop()
        res = prediction_strategy(pc + Bits(32)(4),resFromALU)

        pass



def prediction_strategy(next_pc:Value,alu_res:Value):
    res = (next_pc < alu_res).select(next_pc , alu_res)
    return res
from decoder import *
from utils import ValArray

class ICache(Module):
    def __init__(self, cacheSize: int, init_file):
        self.cacheSize = cacheSize
        self.cachePool = ValArray(Bits(32), cacheSize, self)
        self.id = ValArray(Bits(32), cacheSize, self)
        self.sram = SRAM(32, 16384, init_file)
        super().__init__(ports={
            'start':Port(Bits(1)),
            'flushTag':Port(Bits(1)),
            'newPC':Port(Bits(32))
        })

    @module.combinational
    def build(self, rs, rob):
        pc = RegArray(Bits(32), 1)
        pc_cache = RegArray(Bits(32), 1)
        robId = RegArray(Bits(32), 1, [1])
        start = self.start.peek()
        re = RegArray(Bits(1), 1)
        lastInst = RegArray(Bits(32), 1)

        valid = Bits(1)(0)
        for i in range(rs.rsSize):
            valid = valid | (~rs.busy[i])

        with Condition(start):
            # flush
            flush = self.flushTag.valid()
            with Condition(flush):
                self.flushTag.pop()
                newPC = self.newPC.pop()
                (pc & self)[0] <= newPC
                (pc_cache & self)[0] <= newPC
                for i in range(self.cacheSize):
                    self.cachePool[i] = Bits(32)(0)
                    self.id[i] = Bits(32)(0)
                (re & self)[0] <= Bits(1)(0)
                (lastInst & self)[0] <= self.sram.dout[0]

            with Condition(~flush):
                self.sram.build(Bits(1)(0), re[0], pc_cache[0], Bits(32)(0))
                hasValue = (self.sram.dout[0] != Bits(32)(0)) & (self.sram.dout[0] != lastInst[0])
                cnt = Bits(32)(0)
                inst = Bits(32)(0)
                for i in range(self.cacheSize):
                    zero = self.id[i] == Bits(32)(0)
                    changeInst = (self.id[i] == pc[0] + Bits(32)(1)) & valid
                    # log('!!! {} {} {} {}', Bits(32)(i), changeInst, self.cachePool[i][1][0], self.cachePool[i][0][0])
                    inst = changeInst.select(self.cachePool[i], inst)

                    newValue0 = self.cachePool[i]
                    newValue0 = (zero & hasValue).select(self.sram.dout[0], newValue0)
                    newValue0 = changeInst.select(Bits(32)(0), newValue0)
                    self.cachePool[i] = newValue0

                    newValue1 = self.id[i]
                    newValue1 = (zero & hasValue).select(pc_cache[0], newValue1)
                    newValue1 = changeInst.select(Bits(32)(0), newValue1)
                    self.id[i] = newValue1

                    cnt = cnt + (~zero)
                    hasValue = zero.select(Bits(1)(0), hasValue)

                with Condition(self.sram.dout[0] != Bits(32)(0)):
                    (lastInst & self)[0] <= self.sram.dout[0]
                (re & self)[0] <= (cnt <= Bits(32)(self.cacheSize - 1))

                log("{} {} {}", cnt, inst, self.sram.dout[0])

                (pc_cache & self)[0] <= pc_cache[0] + (cnt <= Bits(32)(self.cacheSize - 1))
                (pc & self)[0] <= pc[0] + (inst != Bits(32)(0))

                with Condition(inst != Bits(32)(0)):
                    # issue into rs
                    res = parseInst(inst)
                    log("issue {}", robId[0])
                    res.print()
                    rs.type.push(res.type)
                    rs.id.push(res.id)
                    rs.rd.push(res.rd)
                    rs.rs1.push(res.rs1)
                    rs.rs2.push(res.rs2)
                    rs.imm.push(res.imm)
                    rs.newId.push(robId[0])

                    # issue into rob
                    rob.type.push(res.type)
                    rob.id.push(res.id)
                    rob.rd.push(res.rd)
                    rob.rs1.push(res.rs1)
                    rob.rs2.push(res.rs2)
                    rob.imm.push(res.imm)
                    rob.newId.push(robId[0])

                    # branch prediction(currently, pc=pc+4)
                    with Condition(res.type == Bits(32)(5)):
                        rob.expectV.push(Bits(32)(0))
                        rob.otherPC.push(pc[0] + (bitsToInt(res.imm, 13, 32) >> Bits(32)(2)))
                    with Condition(res.type != Bits(32)(5)):
                        rob.expectV.push(Bits(32)(0))
                        rob.otherPC.push(Bits(32)(0))

                    (robId & self)[0] <= robId[0] + Bits(32)(1)

        rs.async_called()
        rob.async_called()
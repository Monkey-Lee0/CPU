from decoder import *
from utils import ValArray
from predictor import predictor

class ICache(Module):
    def __init__(self, cacheSize: int, init_file):
        self.cacheSize = cacheSize
        self.cachePool = ValArray(Bits(32), cacheSize, self)
        self.instPC = ValArray(Bits(32), cacheSize, self)
        self.sram = SRAM(32, 16384, init_file)
        self.l = RegArray(Bits(32), 1)
        self.r = RegArray(Bits(32), 1)
        super().__init__(ports={
            'start':Port(Bits(1)),
            'flushTag':Port(Bits(1)),
            'newPC':Port(Bits(32)),
            'newId':Port(Bits(32))
        })

    def push(self, value, pc):
        (self.r & self)[0] <= (self.r[0] + Bits(32)(1)) % Bits(32)(self.cacheSize)
        self.cachePool[self.r[0]] = value
        self.instPC[self.r[0]] = pc

    def clear(self, pos):
        self.cachePool[pos] <= Bits(32)(0)
        self.instPC[pos] = Bits(32)(0)

    def pop(self):
        (self.l & self)[0] <= (self.l[0] + Bits(32)(1)) % Bits(32)(self.cacheSize)
        self.clear(self.l[0])

    @module.combinational
    def build(self, rs, rob):
        pc_cache = RegArray(Bits(32), 1)
        robId = RegArray(Bits(32), 1, [1])
        start = self.start.peek()
        lastInst = RegArray(Bits(32), 1)

        flush = self.flushTag.valid()
        re = start & (~flush) & ((self.l[0] + Bits(32)(1)) % Bits(32)(self.cacheSize) != self.r[0])
        self.sram.build(Bits(1)(0), re, pc_cache[0], Bits(32)(0))

        with (Condition(start)):
            # flush
            with Condition(flush):
                self.flushTag.pop()
                newPC = self.newPC.pop()
                newId = self.newId.pop()

                (pc_cache & self)[0] <= newPC
                (lastInst & self)[0] <= self.sram.dout[0]
                (robId & self)[0] <= newId + Bits(32)(1)

                (self.l & self)[0] <= Bits(32)(0)
                (self.r & self)[0] <= Bits(32)(0)

                for i in range(self.cacheSize):
                    self.clear(i)

            with Condition(~flush):
                valid = Bits(1)(0)
                for i in range(rs.rsSize):
                    valid = valid | (~rs.busy[i])
                valid = valid & (rob.l[0] != (rob.r[0] + Bits(32)(1)) % Bits(32)(rob.robSize)) & (self.l[0] != self.r[0])

                # read from sram
                hasValue = (self.sram.dout[0] != Bits(32)(0)) & (self.sram.dout[0] != lastInst[0]) & \
                           ((self.l[0] + Bits(32)(1)) % Bits(32)(self.cacheSize) != self.r[0])
                with Condition(hasValue):
                    self.push(self.sram.dout[0], pc_cache[0])

                with Condition(self.sram.dout[0] != Bits(32)(0)):
                    (lastInst & self)[0] <= self.sram.dout[0]

                with Condition(hasValue):
                    curInst = parseInst(self.sram.dout[0])
                    with Condition(curInst.type != Bits(32)(5)):
                        (pc_cache & self)[0] <= pc_cache[0] + Bits(32)(1)
                    with Condition(curInst.type == Bits(32)(5)):
                        curInst = parseInst(self.sram.dout[0])
                        movement = bitsToInt(curInst.imm, 13, 32) >> Bits(32)(2)
                        (pc_cache & self)[0] <= predictor(pc_cache[0] + movement, pc_cache[0] + Bits(32)(1))[1]

                # issue
                with Condition(valid):
                    inst = self.cachePool[self.l[0]]
                    pc = self.instPC[self.l[0]]
                    self.pop()
                    (robId & self)[0] <= robId[0] + Bits(32)(1)

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
                        movement = (bitsToInt(res.imm, 13, 32) >> Bits(32)(2))
                        branch, _, otherPC = predictor(pc + movement, pc + Bits(32)(1))
                        rob.expectV.push(branch.zext(Bits(32)))
                        rob.otherPC.push(otherPC)
                    with Condition(res.type != Bits(32)(5)):
                        rob.expectV.push(Bits(32)(0))
                        rob.otherPC.push(Bits(32)(0))

        rs.async_called()
        rob.async_called()
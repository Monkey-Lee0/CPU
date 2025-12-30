from assassyn.frontend import *
from inst import idToType
from src.utils import popAllPorts
from utils import ValArray

class ROB(Module):
    def __init__(self, robSize):
        super().__init__(ports={
            'type':Port(Bits(32)),
            'id':Port(Bits(32)),
            'rd':Port(Bits(32)),
            'rs1':Port(Bits(32)),
            'rs2':Port(Bits(32)),
            'imm':Port(Bits(32)),
            'newId':Port(Bits(32)),
            'expectV':Port(Bits(32)),
            'otherPC':Port(Bits(32)),
            'resFromALU':Port(Bits(32)),
            'idFromALU':Port(Bits(32))
        })
        self.robSize = robSize
        self.busy = ValArray(Bits(1), robSize, self)
        self.inst = ValArray(Bits(32), robSize, self)
        self.dest = ValArray(Bits(32), robSize, self)
        self.value = ValArray(Bits(32), robSize, self)
        self.expect = ValArray(Bits(32), robSize, self)
        self.anotherPC = ValArray(Bits(32), robSize, self)
        self.ID = ValArray(Bits(32), robSize, self)
        self.l = RegArray(Bits(32), 1, [0])
        self.r = RegArray(Bits(32), 1, [0])


    def push(self, busy, inst, dest, value, newId, expectV, otherPC):
        (self.r & self)[0] <= (self.r[0] + Bits(32)(1)) % Bits(32)(self.robSize)
        self.busy[self.r[0]] = busy
        self.inst[self.r[0]] = inst
        self.dest[self.r[0]] = dest
        self.value[self.r[0]] = value
        self.ID[self.r[0]] = newId
        self.expect[self.r[0]] = expectV
        self.anotherPC[self.r[0]] = otherPC


    def pop(self):
        (self.l & self)[0] <= (self.l[0] + Bits(32)(1)) % Bits(32)(self.robSize)
        self.clear(self.l[0])

    def clear(self, pos:Value):
        self.busy[pos] = Bits(1)(0)
        self.inst[pos] = Bits(32)(0)
        self.dest[pos] = Bits(32)(0)
        self.value[pos] = Bits(32)(0)
        self.ID[pos] = Bits(32)(0)
        self.expect[pos] = Bits(32)(0)
        self.anotherPC[pos] = Bits(32)(0)

    def log(self):
        log('-'*50)
        for i in range(self.robSize):
            log('busy:{} inst:{} dest:{} value:{} expectV:{} anotherPC:{}',
                self.busy[i], self.inst[i], self.dest[i], self.value[i], self.expect[i], self.anotherPC[i])
        log('-'*50)

    @module.combinational
    def build(self, rf, ic, rs):
        flush = RegArray(Bits(1), 1)

        with (Condition(~flush[0])):
            # issue in rob
            with Condition(self.type.valid()):
                instType = self.type.pop()
                instId = self.id.pop()
                rd = self.rd.pop()
                rs1 = self.rs1.pop()
                rs2 = self.rs2.pop()
                imm = self.imm.pop()
                newId = self.newId.pop()
                expect = self.expectV.pop()
                anotherPC = self.otherPC.pop()

                with Condition((instType == Bits(32)(1)) | (instType == Bits(32)(2))):
                    rf.build(rd, rf.regs[rd], newId)
                    self.push(Bits(1)(1), instId, rd, Bits(32)(0), newId, expect, anotherPC)
                with Condition(instType == Bits(32)(5)):
                    self.push(Bits(1)(1), instId, Bits(32)(0), Bits(32)(0), newId, expect, anotherPC)

            # receive value from ALU
            with Condition(self.resFromALU.valid()):
                res = self.resFromALU.pop()
                robId = self.idFromALU.pop()
                log("{} {}", robId, res)
                for i in range(self.robSize):
                    with Condition(self.ID[i] == robId):
                        self.value[i] = res
                        self.busy[i] = Bits(1)(0)

            # commit
            instType = idToType(self.inst[self.l[0]])
            topPrepared = (self.l[0] != self.r[0]) & (~self.busy[self.l[0]])
            log("{} ??? {} {} {}", instType, topPrepared, self.l[0], self.r[0])
            predictionFailed = ((instType == Bits(32)(5)) | (instType == Bits(32)(7))) & \
                (self.value[self.l[0]]!=self.expect[self.l[0]])

            with Condition(topPrepared):
                commitId = self.ID[self.l[0]]
                log("commit {} {}", commitId, self.value[self.l[0]])
                # deliver to rs
                rs.robId.push(commitId)
                rs.robRes.push(self.value[self.l[0]])
                self.pop()
                # modify in rf
                with Condition((instType == Bits(32)(1)) | (instType == Bits(32)(2))):
                    dest = self.dest[self.l[0]]
                    rf.build(dest, self.value[self.l[0]],
                             (rf.dependence[dest] == commitId).select(Bits(32)(0), rf.dependence[dest]))

                with Condition(instType == Bits(32)(5)):
                    log("commit {} {}", commitId, self.value[self.l[0]])

                with Condition(predictionFailed):
                    (flush & self)[0] <= Bits(1)(1)
                    rs.flushTag.push(Bits(1)(1))
                    ic.flushTag.push(Bits(1)(1))
                    ic.newPC.push(self.anotherPC[self.l[0]])

        # flush
        with Condition(flush[0]):
            log("prediction failed, flush")
            popAllPorts(self)
            for i in range(self.robSize):
                self.clear(Bits(32)(i))
            rf.clearDependency()
            (flush & self)[0] <= Bits(1)(0)

        # rf.log()
        # self.log()
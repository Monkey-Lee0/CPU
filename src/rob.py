from assassyn.frontend import *
from inst import idToType
from src.utils import popAllPorts, popWithDefault
from utils import ValArray

class ROB(Module):
    def __init__(self, robSize):
        super().__init__(ports={
            'type':Port(Bits(32)),
            'id':Port(Bits(32)),
            'rd':Port(Bits(32)),
            'newId':Port(Bits(32)),
            'expectV':Port(Bits(32)),
            'otherPC':Port(Bits(32)),
            'val':Port(Bits(32)),
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

    def clear(self, pos):
        self.busy[pos] = Bits(1)(0)
        self.inst[pos] = Bits(32)(0)
        self.dest[pos] = Bits(32)(0)
        self.value[pos] = Bits(32)(0)
        self.ID[pos] = Bits(32)(0)
        self.expect[pos] = Bits(32)(0)
        self.anotherPC[pos] = Bits(32)(0)

    def full(self):
        return ((self.r[0] + Bits(32)(1)) % Bits(32)(self.robSize) == self.l[0]) | \
            ((self.r[0] + Bits(32)(2)) % Bits(32)(self.robSize) == self.l[0])

    def log(self):
        log('-'*50)
        for i in range(self.robSize):
            log('busy:{} inst:{} dest:{} value:{} ID:{} expectV:{} anotherPC:{}',
                self.busy[i], self.inst[i], self.dest[i], self.value[i], self.ID[i], self.expect[i], self.anotherPC[i])
        log('-'*50)

    @module.combinational
    def build(self, rf, ic, rs, lsb, alu):
        flush = RegArray(Bits(1), 1)

        with (Condition(~flush[0])):
            # to check whether issue and commit into the same dest
            issueDest = self.type.valid().select(self.rd.peek(), Bits(32)(0))

            # issue in rob
            with Condition(self.type.valid()):
                instType = self.type.pop()
                instId = self.id.pop()
                rd = self.rd.pop()
                newId = self.newId.pop()
                expect = self.expectV.pop()
                anotherPC = self.otherPC.pop()
                val = popWithDefault(self.val, Bits(32)(0))

                with Condition((instType == Bits(32)(1)) | (instType == Bits(32)(2)) | (instType == Bits(32)(3))):
                    rf.buildDependence(rd, newId)
                    self.push(Bits(1)(1), instId, rd, val, newId, expect, anotherPC)
                with Condition(instType == Bits(32)(4)):
                    self.push(Bits(1)(0), instId, Bits(32)(0), val, newId, expect, anotherPC)
                with Condition(instType == Bits(32)(5)):
                    self.push(Bits(1)(1), instId, Bits(32)(0), val, newId, expect, anotherPC)
                with Condition((instType == Bits(32)(6)) | (instType == Bits(32)(7))):
                    rf.buildDependence(rd, newId)
                    self.push(Bits(1)(0), instId, rd, val, newId, expect, anotherPC)

            # commit
            commitId = self.ID[self.l[0]]
            instType = idToType(self.inst[self.l[0]])
            topPrepared = (self.l[0] != self.r[0]) & (~self.busy[self.l[0]])
            lsbPrepared = instType != Bits(32)(4)
            for i in range(lsb.lsbSize):
                # log("lsb.status[i]:{}, lsb.robId[i]:{}", lsb.status[i], lsb.robId[i])
                lsbPrepared = lsbPrepared | ((lsb.status[i] == Bits(32)(3)) & (lsb.robId[i] == commitId))
            topPrepared = topPrepared & lsbPrepared
            predictionFailed = ((instType == Bits(32)(5)) & (self.value[self.l[0]] != self.expect[self.l[0]])) | (
                self.inst[self.l[0]] == Bits(32)(35))

            with Condition(topPrepared):
                log("commit {} {}", commitId, self.value[self.l[0]])
                self.pop()
                # modify in rs
                rs.accept(commitId, self.value[self.l[0]])
                rs.robId.push(commitId)
                rs.robRes.push(self.value[self.l[0]])
                # modify in rf
                with Condition((instType == Bits(32)(1)) | (instType == Bits(32)(2)) | (instType == Bits(32)(3)) |
                               (instType == Bits(32)(6)) | (instType == Bits(32)(7))):
                    dest = self.dest[self.l[0]]
                    rf.buildValue(dest, self.value[self.l[0]])
                    with Condition((rf.dependence[dest] == commitId) & (dest != issueDest)):
                        rf.buildDependence(dest, Bits(32)(0))

                # enable in lsb
                with Condition(instType == Bits(32)(4)):
                    lsb.newId_rob.push(commitId)
                    lsb.robFlag.push(Bits(1)(1))

                with Condition(predictionFailed):
                    (flush & self)[0] <= Bits(1)(1)
                    rs.flushTag.push(Bits(1)(1))
                    ic.flushTag.push(Bits(1)(1))
                    ic.newPC.push(self.anotherPC[self.l[0]])
                    log("fuck {}", self.anotherPC[self.l[0]])
                    ic.newId.push(self.ID[self.l[0]])
                    lsb.flushTag.push(Bits(1)(1))
                    lsb.flushId.push(self.ID[self.l[0]])
                    alu.flushTag.push(Bits(1)(1))

        # flush
        with Condition(flush[0]):
            log("prediction failed, flush")
            popAllPorts(self)
            for i in range(self.robSize):
                self.clear(i)
            (self.l & self)[0] <= Bits(32)(0)
            (self.r & self)[0] <= Bits(32)(0)
            rf.clearDependency()
            (flush & self)[0] <= Bits(1)(0)

        # rf.log()
        self.log()
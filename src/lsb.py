from assassyn.frontend import *
from utils import ValArray

def isRead(instId):
    return (instId >= Bits(32)(20)) & (Bits(32)(24) >= instId)

def isWrite(instId):
    return (instId >= Bits(32)(25)) & (Bits(32)(27) >= instId)

class LSB(Module):
    def __init__(self, lsbSize):
        super().__init__(ports={
            # ports from icache
            'newId_ic':Port(Bits(32)),
            'inst_id':Port(Bits(32)),
            # ports from rs
            'newId_rs':Port(Bits(32)),
            'wdata':Port(Bits(32)),
            # ports from agu
            'newId_agu':Port(Bits(32)),
            'newAddr':Port(Bits(32)),
            # ports from rob
            'newId_rob':Port(Bits(32)),
            'robFlag':Port(Bits(1)),
            'flushTag':Port(Bits(1)),
            'flushId':Port(Bits(32)),
        })
        self.lsbSize = lsbSize
        self.robId = ValArray(Bits(32), lsbSize, self)
        self.instId = ValArray(Bits(32), lsbSize, self)
        self.addr = ValArray(Bits(32), lsbSize, self)
        self.value = ValArray(Bits(32), lsbSize, self)
        self.status = ValArray(Bits(32), lsbSize, self)
        # 0 -> empty
        # 1 -> decoder received
        # 2 -> rs received
        # 3 -> agu received
        # 4 -> rob enabled / read request sent

    @module.combinational
    def build(self, dCache, rob):
        flush = self.flushTag.valid()

        # branch prediction failed, flush!
        with Condition(flush):
            pass

        with Condition(~flush):
            # new item from decoder(decoder needs to check full or not)
            with Condition(self.newId_ic.valid()):
                newId = self.newId_ic.pop()
                instId = self.inst_id.pop()
                flag = Bits(1)(1)
                for i in range(self.lsbSize):
                    validItem = ~self.status[i]
                    with Condition(flag & validItem):
                        self.robId[i] = newId
                        self.instId[i] = instId
                        self.status[i] = Bits(32)(1)
                    flag = flag & (~validItem)

            # write data from rs
            with Condition(self.newId_rs.valid()):
                newId = self.newId_rs.pop()
                wdata = self.wdata.pop()
                for i in range(self.lsbSize):
                    with Condition(self.robId[i] == newId):
                        self.value[i] = wdata
                        self.status[i] = Bits(32)(2)

            # addr from agu
            with Condition(self.newId_agu.valid()):
                newId = self.newId_agu.pop()
                addr = self.newAddr.pop()
                for i in range(self.lsbSize):
                    with Condition(self.robId[i] == newId):
                        self.status[i] = Bits(32)(3)
                        self.addr[i] = addr

            # enabling flag from rob
            with Condition(self.newId_rob.valid()):
                newId = self.newId_rob.pop()
                robFlag = self.robFlag.pop()
                for i in range(self.lsbSize):
                    with Condition(self.robId[i] == newId):
                        self.status[i] = Bits(32)(4)

            # send request to dcache
            sentToCache = Bits(1)(0)
            sentToRob = Bits(1)(0)
            for i in range(self.lsbSize):
                with Condition(isWrite(self.instId[i])):
                    with Condition((self.status[i] == Bits(32)(4)) & (~sentToCache)):
                        dCache.newAddr.push(self.addr[i])
                        dCache.newType.push(Bits(1)(1))
                        dCache.wdata.push(self.value[i])
                        self.clear(i)

                with Condition(isRead(self.instId[i])):
                    with Condition((self.status[i] == Bits(32)(4)) & (~sentToRob)):
                        hasItem, itemStatus, value = dCache.getItem(self.addr[i])
                        with Condition(itemStatus):
                            rob.resFromLSB.push(value)
                            rob.idFromLSB.push(self.robId[i])
                            self.clear(i)
                    with Condition((self.status[i] == Bits(32)(3)) & (~sentToCache) &
                                   (~self.checkDependency(self.addr[i], self.robId[i]))):
                        dCache.newAddr.push(self.addr[i])
                        dCache.newType.push(Bits(1)(0))
                        dCache.wdata.push(0)
                        self.status[i] = Bits(32)(4)

                sentToCache = sentToCache | (isWrite(self.instId[i]) & (self.status[i] == Bits(32)(4))) | (
                    isRead(self.instId[i]) & (self.status[i] == Bits(32)(3)) & (
                    ~self.checkDependency(self.addr[i], self.robId[i])))
                sentTORob = sentToRob | (isRead(self.instId[i]) & (self.status[i] == Bits(32)(4)) &
                                         dCache.getItem(self.addr[i])[1])

    def clear(self, index:int):
        self.robId[index] = Bits(32)(0)
        self.instId[index] = Bits(32)(0)
        self.addr[index] = Bits(32)(0)
        self.value[index] = Bits(32)(0)
        self.status[index] = Bits(32)(0)

    def checkDependency(self, addr, robId):
        hasDependency = Bits(1)(0)
        for i in range(self.lsbSize):
            hasDependency = hasDependency | (self.status[i] & (self.robId[i] < robId) & (
                    self.addr[i] == addr) & isWrite(self.instId[i]))
        return hasDependency

    def log(self):
        log('-'*50)
        for i in range(self.lsbSize):
            log('robId:{} addr:{} re:{} we:{} value:{} enabled:{}', self.robId[i], self.addr[i], self.re[i],
                self.we[i], self.value[i], self.enabled[i])
        log('-'*50)
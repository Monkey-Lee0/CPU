from assassyn.frontend import *

from utils import ValArray, bitsToInt32

def isRead(instId):
    return (instId >= Bits(32)(20)) & (Bits(32)(24) >= instId)

def isWrite(instId):
    return (instId >= Bits(32)(25)) & (Bits(32)(27) >= instId)

def resolve_lbu(offset, value):
    l = offset << Bits(32)(3)
    return (value >> l) & Bits(32)(0xFF)

def resolve_lb(offset, value):
    l = offset << Bits(32)(3)
    return (bitsToInt32((value >> l) & Bits(32)(0xFF),8)).bitcast(Bits(32))

def resolve_lhu(offset, value):
    l = offset << Bits(32)(3)
    return (value >> l) & Bits(32)(0xFFFF)

def resolve_lh(offset, value):
    l = offset << Bits(32)(3)
    return (bitsToInt32((value >> l) & Bits(32)(0xFFFF),16)).bitcast(Bits(32))

def resolve_sb(newData, offset, Val):
    Modification = newData & Bits(32)(0xFF)
    bit_offset = offset << Bits(32)(3)
    clear_mask = ~(Bits(32)(0xFF) << bit_offset)
    val_cleared = Val & clear_mask
    mod_shifted = Modification << bit_offset
    result = val_cleared | mod_shifted
    return result

def resolve_sh(newData, offset, Val):
    Modification = newData & Bits(32)(0xFFFF)
    bit_offset = offset << Bits(32)(3)
    clear_mask = ~(Bits(32)(0xFFFF) << bit_offset)
    val_cleared = Val & clear_mask
    mod_shifted = Modification << bit_offset
    result = val_cleared | mod_shifted
    return result


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
        self.offset = ValArray(Bits(32), lsbSize, self)
        self.value = ValArray(Bits(32), lsbSize, self)
        self.status = ValArray(Bits(32), lsbSize, self)
        # 0 -> empty
        # 1 -> decoder received
        # 2 -> rs received
        # 3 -> agu received
        # 4 -> rob enabled / read request sent
        # 5 -> read request sent(for sb, sh)
        # 6 -> wait for a cycle(for sb, sh)

    @module.combinational
    def build(self, dCache, rob):
        flush = self.flushTag.valid()

        # branch prediction failed, flush!
        with Condition(flush):
            self.flushTag.pop()
            id = self.flushId.pop()
            for i in range(self.lsbSize):
                with Condition(self.robId[i] >= id):
                    self.clear(i)

        with Condition(~flush):
            # new item from decoder(decoder needs to check full or not)
            with Condition(self.newId_ic.valid()):
                newId = self.newId_ic.pop()
                instId = self.inst_id.pop()
                flag = Bits(1)(1)
                for i in range(self.lsbSize):
                    validItem = self.status[i] == Bits(32)(0)
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
                        self.addr[i] = addr >> Bits(32)(2)
                        self.offset[i] = addr & Bits(32)(3)

            # enabling flag from rob
            with Condition(self.newId_rob.valid()):
                newId = self.newId_rob.pop()
                self.robFlag.pop()
                for i in range(self.lsbSize):
                    with Condition(self.robId[i] == newId):
                        self.status[i] = Bits(32)(4)

            # send request to dcache
            sentToCache = Bits(1)(0)
            sentToRob = Bits(1)(0)
            for i in range(self.lsbSize):
                with Condition(isWrite(self.instId[i])):
                    with Condition((self.status[i] == Bits(32)(4)) & (~sentToCache)):
                        with Condition(self.instId[i] == Bits(32)(27)):
                            dCache.newAddr.push(self.addr[i])
                            dCache.wdata.push(self.value[i])
                            dCache.newType.push(Bits(1)(1))
                            self.clear(i)
                        with Condition(self.instId[i] != Bits(32)(27)):
                            hasItem, _, _ = dCache.getItem(self.addr[i])
                            with Condition(~hasItem):
                                dCache.newAddr.push(self.addr[i])
                                dCache.wdata.push(Bits(32)(0))
                                dCache.newType.push(Bits(1)(0))
                            self.status[i] = Bits(32)(5)
                    with Condition((self.status[i] == Bits(32)(5)) & (~sentToCache)):
                        hasItem, itemStatus, value = dCache.getItem(self.addr[i])
                        with Condition(itemStatus):
                            value = (self.instId[i] == Bits(32)(25)).select(
                                resolve_sb(self.value[i], self.offset[i], value), value)
                            value = (self.instId[i] == Bits(32)(26)).select(
                                resolve_sh(self.value[i], self.offset[i], value), value)
                            dCache.newAddr.push(self.addr[i])
                            dCache.wdata.push(value)
                            dCache.newType.push(Bits(1)(1))
                            self.status[i] = Bits(32)(6)
                    with Condition(self.status[i] == Bits(32)(6)):
                        self.clear(i)

                with Condition(isRead(self.instId[i])):
                    with Condition((self.status[i] == Bits(32)(4)) & (~sentToRob)):
                        hasItem, itemStatus, value = dCache.getItem(self.addr[i])
                        value = (self.instId[i] == Bits(32)(20)).select(resolve_lb(self.offset[i],value),value)
                        value = (self.instId[i] == Bits(32)(21)).select(resolve_lbu(self.offset[i],value),value)
                        value = (self.instId[i] == Bits(32)(22)).select(resolve_lh(self.offset[i],value),value)
                        value = (self.instId[i] == Bits(32)(23)).select(resolve_lhu(self.offset[i],value),value)
                        with Condition(itemStatus == Bits(32)(1)):
                            # modify in rob
                            for j in range(rob.robSize):
                                with Condition(rob.ID[j] == self.robId[i]):
                                    rob.value[j] = value
                                    rob.busy[j] = Bits(1)(0)
                            self.clear(i)

                    with Condition((self.status[i] == Bits(32)(3)) & (~sentToCache) &
                                   (~self.checkDependency(self.addr[i], self.robId[i]))):
                        dCache.newAddr.push(self.addr[i])
                        dCache.wdata.push(Bits(32)(0))
                        dCache.newType.push(Bits(1)(0))
                        self.status[i] = Bits(32)(4)

                sentToCache = sentToCache | (isWrite(self.instId[i]) & (self.status[i] >= Bits(32)(4))) | (
                    isRead(self.instId[i]) & (self.status[i] == Bits(32)(3)) & (
                    ~self.checkDependency(self.addr[i], self.robId[i])))
                sentToRob = sentToRob | (isRead(self.instId[i]) & (self.status[i] == Bits(32)(4)) &
                                         (dCache.getItem(self.addr[i])[1] == Bits(32)(1)))

        dCache.async_called()

    def clear(self, index:int):
        self.robId[index] = Bits(32)(0)
        self.instId[index] = Bits(32)(0)
        self.addr[index] = Bits(32)(0)
        self.value[index] = Bits(32)(0)
        self.status[index] = Bits(32)(0)

    def checkDependency(self, addr, robId):
        hasDependency = Bits(1)(0)
        for i in range(self.lsbSize):
            hasDependency = hasDependency | ((self.status[i] != Bits(32)(0)) & (self.robId[i] < robId) & (
                    self.addr[i] == addr) & isWrite(self.instId[i]))
        return hasDependency

    def log(self):
        log('-'*50)
        for i in range(self.lsbSize):
            log('robId:{} addr:{} re:{} we:{} value:{} enabled:{}', self.robId[i], self.addr[i], self.re[i],
                self.we[i], self.value[i], self.enabled[i])
        log('-'*50)

    def full(self):
        cnt = Bits(32)(0)
        for i in range(self.lsbSize):
            cnt = cnt + (self.status[i] == Bits(32)(0)).bitcast(Bits(32))
        return Bits(32)(2) >= cnt
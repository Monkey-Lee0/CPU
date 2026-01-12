from decoder import *
from utils import ValArray, peekWithDefault, checkInside
from predictor import predictor
from assassyn.frontend import *
from assassyn.ir.expr.intrinsic import get_mem_resp

class ICache(Module):
    def __init__(self, cacheSize: int, init_file):
        super().__init__(ports={
            'start':Port(Bits(1)),
            'flushTag':Port(Bits(1)),
            'newPC':Port(Bits(32)),
            'newId':Port(Bits(32))
        })
        self.cacheSize = cacheSize
        self.cachePool = ValArray(Bits(32), cacheSize, self)
        self.instPC = ValArray(Bits(32), cacheSize, self)
        self.sram = SRAM(32, 16384, init_file)
        self.l = RegArray(Bits(32), 1)
        self.r = RegArray(Bits(32), 1)

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
    def build(self, rs, rob, lsb):
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
                for i in range(lsb.lsbSize):
                    valid = valid | (lsb.status[i] == Bits(32)(0))
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
                        movement = bitsToInt32(curInst.imm, 13) >> Bits(32)(2)
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
                    rs.inst_type.push(res.type)
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

                    # issue into lsb
                    with Condition((res.id >= Bits(32)(20)) & (Bits(32)(27) >= res.id)):
                        lsb.newId_ic.push(robId[0])
                        lsb.inst_id.push(res.id)

                    # branch prediction(currently, pc=pc+4)
                    with Condition(res.type == Bits(32)(5)):
                        movement = (bitsToInt32(res.imm, 13) >> Bits(32)(2))
                        branch, _, otherPC = predictor(pc + movement, pc + Bits(32)(1))
                        rob.expectV.push(branch.zext(Bits(32)))
                        rob.otherPC.push(otherPC)
                    with Condition(res.type != Bits(32)(5)):
                        rob.expectV.push(Bits(32)(0))
                        rob.otherPC.push(Bits(32)(0))

        rs.async_called()
        rob.async_called()

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
    bit_offset = offset << Bits(32)(4)
    clear_mask = ~(Bits(32)(0xFFFF) << bit_offset)
    val_cleared = Val & clear_mask
    mod_shifted = Modification << bit_offset
    result = val_cleared | mod_shifted
    return result

class DCache(Module):
    def __init__(self, cacheSize, init_file):
        super().__init__(ports={
            'newAddr':Port(Bits(32)),
            'wdata':Port(Bits(32)),
            'offset':Port(Bits(32)),
            'instID':Port(Bits(32)) # sb(ljy)-25 ; sh-26 ; sw-27
        })
        self.cacheSize = cacheSize
        self.sram = SRAM(32, 16384, init_file)
        self.itemAddr = ValArray(Bits(32), cacheSize, self)
        self.itemValue = ValArray(Bits(32), cacheSize, self)
        self.itemStatus = ValArray(Bits(32), cacheSize, self) # 0-request not sent; 1-value prepared
        self.l = RegArray(Bits(32), 1)
        self.r = RegArray(Bits(32), 1)

    def full(self):
        return (self.r[0] + Bits(32)(1)) % Bits(32)(self.cacheSize) == self.l[0]

    def empty(self):
        return self.l[0] == self.r[0]

    def push(self, newAddr, newValue, prepared):
        (self.r & self)[0] <= (self.r[0] + Bits(32)(1)) % Bits(32)(self.cacheSize)
        self.itemAddr[self.r[0]] = newAddr
        self.itemValue[self.r[0]] = newValue
        self.itemStatus[self.r[0]] = prepared

    def pop(self):
        (self.l & self)[0] <= (self.l[0] + Bits(32)(1)) % Bits(32)(self.cacheSize)
        self.itemAddr[self.l[0]] = Bits(32)(0)
        self.itemValue[self.l[0]] = Bits(32)(0)
        self.itemStatus[self.l[0]] = Bits(32)(0)

    def getItem(self, myAddr):
        hasItem = Bits(1)(0)
        itemStatus = Bits(32)(0)
        value = Bits(32)(0)
        for i in range(self.cacheSize):
            hit = (myAddr == self.itemAddr[i]) & checkInside(self.l[0], self.r[0], Bits(32)(i))
            hasItem = hasItem | hit
            itemStatus = itemStatus | hit.select(self.itemStatus[i], Bits(32)(0))
            value = hit.select(self.itemValue[i], value)

        return hasItem, itemStatus, value

    @module.combinational
    def build(self):
        # write when full, top priority
        we = self.full()
        addr_we = self.itemAddr[self.l[0]]
        wdata = self.itemValue[self.l[0]]
        lastAddr = RegArray(Bits(32), 1)

        with Condition(self.full()):
            self.pop()

        # request old read, second top priority
        re_old = Bits(1)(0)
        addr_re_old = Bits(32)(0)
        for i in range(self.cacheSize):
            inside = checkInside(self.l[0], self.r[0], Bits(32)(i))
            addr_re_old = ((~re_old) & (self.itemStatus[i] == Bits(32)(0)) & inside).select(
                self.itemAddr[i], addr_re_old)
            re_old = re_old | ((self.itemStatus[i] == Bits(32)(0)) & inside)
        re_old = re_old & (~we)

        # request new read, last top priority
        newAddr = peekWithDefault(self.newAddr, Bits(32)(0))
        newData = peekWithDefault(self.wdata, Bits(32)(0))
        offset = peekWithDefault(self.offset, Bits(32)(0))
        instID = peekWithDefault(self.instID, Bits(32)(0))
        newType = (instID >= Bits(32)(20)) & (Bits(32)(26) >= instID) # read-0 ; write-1 (sb, sh both need to read before write)
        hasItem = (~self.newAddr.valid()) | self.getItem(newAddr)[0]
        re_new = (~we) & (~re_old) & (~hasItem) & (~newType)
        addr_re_new = newAddr
        with Condition(self.newAddr.valid()):
            self.newAddr.pop()
            self.wdata.pop()
            self.offset.pop()
            self.instID.pop()
            # log('hillo {} {} {} {} {}', newAddr, newType, newData, hasItem, re_new)
            with Condition(~hasItem):
                with Condition(newType):
                    self.push(newAddr, newData, Bits(32)(1))
                with Condition(~newType):
                    self.push(newAddr, Bits(32)(0), Bits(32)(0))

        addr_dram = we.select(addr_we, re_old.select(addr_re_old, re_new.select(addr_re_new, Bits(32)(0))))
        re = re_old | re_new
        # log("{} {} {} {} {}", we, re, addr_dram, wdata, lastAddr[0])
        # self.log()
        self.sram.build(we, re, addr_dram, wdata)
        (lastAddr & self)[0] <= addr_dram

        for i in range(self.cacheSize):
            with Condition((self.itemAddr[i] == lastAddr[0]) & (self.itemStatus[i] == Bits(32)(0)) &
                           checkInside(self.l[0], self.r[0], Bits(32)(i))):
                self.itemStatus[i] = Bits(32)(1)
                Val = self.sram.dout[0]
                Val = (instID == Bits(32)(25)).select(resolve_sb(newData, offset, Val), Val)
                Val = (instID == Bits(32)(26)).select(resolve_sh(newData, offset, Val), Val)
                Val = (instID == Bits(32)(27)).select(newData, Val)
                self.itemValue[i] = Val


    def log(self):
        log('-'*50)
        log('range: {} {}', self.l[0], self.r[0])
        for i in range(self.cacheSize):
            log('{} {} {}', self.itemAddr[i], self.itemValue[i], self.itemStatus[i])
        log('-'*50)
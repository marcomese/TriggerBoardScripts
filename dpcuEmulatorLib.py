# -*- coding: utf-8 -*-

from paramiko import SSHClient, AutoAddPolicy, SSHException
import re
from valNameRegs import valNameRegs
from regNameRegs import regNameRegs
from time import time,localtime
from datetime import date

spwWriteRespPattern = "@\s*(?:[a-zA-Z0-9]{8})\s*=\s*([a-zA-Z0-9]{8})(?=\\n)?"
spwWriteRespRegex = re.compile(spwWriteRespPattern)

spwRespPattern = "0x([a-zA-Z0-9]{8})(?=\\n)?"
spwRespRegex = re.compile(spwRespPattern)

MSBreg = 0
LSBreg = 1
firstBitL = 2
lastBitL = 3
nBits = 4

CMD_REG_ADDR = "00000008"

CIT_PWR_MASK = "FFFFFFCF"

GENERIC_MASK = "00000008"

START_DEBUG = 6
APPLY_TRG_MASK = 7
APPLY_PMT_MASK = 8
START_ACQ = 9
STOP_ACQ = 10
START_CAL = 11
STOP_CAL = 12
APPLY_PEDESTALS = 14

CIT = { # valori per applyConfiguration
       "CIT0" : 1,
       "CIT1" : 2,
       "ALL"  : 3
       }

invertedParams = "TCONST_HG_SHAPER|TCONST_LG_SHAPER|DAC[0-9][0-9](?!_IN)(_T)*"

invParamsRegex = re.compile(invertedParams)

invRegNameRegs = {v:k for k,v in regNameRegs.items()}

def genRegList(valN):
    regList = (
            valNameRegs[valN][MSBreg],
            valNameRegs[valN][LSBreg],
            )
    
    return regList

def genMasks(valN,val):
    numOfRegs = valNameRegs[valN][MSBreg]-valNameRegs[valN][LSBreg] + 1
    lenFirstBits = len(valNameRegs[valN][firstBitL])
    lenLastBits = len(valNameRegs[valN][lastBitL])
    numOfBits = valNameRegs[valN][nBits]
    
    if lenLastBits != lenFirstBits:
        raise Exception("Errore nella definizione di valNameRegs!"
                        " La lunghezza delle liste lastBits e firstBits"
                        " deve essere uguale!")
    
    if numOfRegs < 0:
        raise Exception("Errore nella definizione di valNameRegs!"
                        " Il registro MSB deve avere un valore numerico "
                        " maggiore di quello LSB!")
    elif numOfRegs > 2:
        raise Exception("Errore nella definizione di valNameRegs!"
                        " Il numero di registri a 32bit che può occupare"
                        " un parametro (con un numero di bit < 32)"
                        " non può essere maggiore di 2!")
    
    maxVal = (2**numOfBits)-1
    
    if val > maxVal:
        raise Exception("Errore! Inserire un numero da 0 a {}".format(maxVal))
    
    regMasks = []
    valMasks = []
    
    valToBits = "{:0{numBits}b}".format(val,numBits = numOfBits)
    
    for n in range(numOfRegs):
        maskStr = ""
        valMaskStr = ""
        
        firstBitPos = valNameRegs[valN][firstBitL][n]
        lastBitPos = valNameRegs[valN][lastBitL][n]
        
        numOfBitsN = firstBitPos - lastBitPos + 1
        
        if numOfBitsN < 0:
            raise Exception("Errore nella definizione di valNameRegs!"
                            " La posizione del first bit deve essere maggiore"
                            " di quella del last bit")
        
        maskStr += '1' * (31 - firstBitPos)
        maskStr += '0' * numOfBitsN
        maskStr += '1' * (lastBitPos)

        regMasks.append(int(maskStr,2))

        msb = 1-n

        lastValIndex = (n*numOfBits) + (msb*numOfBitsN)
        firstValIndex = n*(numOfBits-numOfBitsN)
        
        # non è possibile fare semplicemente val << lastBitPos perchè
        # il valore può spezzarsi fra due registri
        valMaskStr += '0' * (31 - firstBitPos)        
        valMaskStr += valToBits[firstValIndex:lastValIndex]
        valMaskStr += '0' * (lastBitPos)
        
        valMaskN = int(valMaskStr,2)
        
        valMasks.append(valMaskN)
    
    return regMasks,valMasks

class dpcuEmulator(object):
    def __init__(self, dpcuEmAddr):
        try:
            self.ssh = SSHClient()
            self.ssh.set_missing_host_key_policy(AutoAddPolicy())
            
            self.ssh.connect(dpcuEmAddr,
                             username = 'root',
                             password = 'root',
                             timeout = 10)
            
            _, stdOut, _ = self.ssh.exec_command('ls')
            if 'sd' not in stdOut.read().decode('utf-8'):
                self.ssh.exec_command('mkdir sd && mount /dev/mmcblk0p1 sd')
            
            ########## FIX ###########
            _, regVal = self.readReg("00000005")
            if regVal != "00000000":
                print(f"SANDBOX TEST FAILED: read {regVal}")
                self.writeReg("00000005","00000000")
                self.writeReg("00000005","00000000")
            ###########################

        except SSHException:
            print("Errore nella connessione ssh!")
            self.ssh = None

    def _readExecFeedback(f):
        def wrapper(self, *args, **kwargs):
            _, fRes, _ = f(self,*args,**kwargs)
            
            spwRespStr = spwRespRegex.findall(fRes.read().decode('utf-8'))
            
            if len(spwRespStr) == 2:
                return (spwRespStr[1],spwRespStr[0])
            else:
                return [(ss[1],ss[0]) for ss in list(zip(*[iter(spwRespStr)]*2))]
        
        return wrapper

    def _readCmdFeedback(f):
        def wrapper(self,feedback=False):
            if feedback is False:
                return f(self)
            else:
                firstResp, secResp = f(self)

                print(f"@{firstResp[0]} = {firstResp[1]}")
                print(f"@{secResp[0]} = {secResp[1]}")
                
                return firstResp, secResp

        return wrapper

    def _readWRegFeedback(f):
        def wrapper(self, *args, **kwargs):
            fRes = f(self,*args)
            fResLen = len(fRes)

            if 'feedback' in kwargs.keys() and kwargs['feedback'] is True:
                for i,fr in enumerate(fRes):
                    if type(fr) == tuple:
                        print(f"@{fr[0]} = {fr[1]}")
                    elif type(fr) == str:
                        if i != fResLen-1:
                            print(f"@{fRes[i]} = {fRes[i+1]}")
            
            return fRes
        
        return wrapper

    def writeReg(self, addr, data):
        self.ssh.exec_command(f"sd/map -l 0x40c40004 =0x{addr}", timeout = 10)
        self.ssh.exec_command(f"sd/map -l 0x40c40008 =0x{data}", timeout = 10)
        self.ssh.exec_command("sd/map -l 0x40c40010 =0x0", timeout = 10)
        self.ssh.exec_command("sd/map -l 0x40c40010 =0xC", timeout = 10)
        self.ssh.exec_command("sd/map -l 0x40c40010 =0x3", timeout = 10)
        self.ssh.exec_command("sd/map -l 0x40c40010 =0x0", timeout = 10)
        _, respAddr, _ = self.ssh.exec_command("sd/map -l 0x40c40004", timeout = 10)
        _, respData, _ = self.ssh.exec_command("sd/map -l 0x40c4000C", timeout = 10)
        
        respAddrStr = spwWriteRespRegex.findall(respAddr.read().decode('utf-8'))[0]
        respDataStr = spwWriteRespRegex.findall(respData.read().decode('utf-8'))[0]
        
        return (respAddrStr,respDataStr)

    @_readExecFeedback
    def readReg(self, addr):
        addrInt = int(addr,16)
        return self.ssh.exec_command(f"sd/spwTest_read_write -t R -a {addrInt}", timeout = 10)

    @_readExecFeedback
    def burstRead(self, startAddr, nData):
        startAddrInt = int(startAddr,16)
        return self.ssh.exec_command(f"sd/spwTest_read_write -t B -a {startAddrInt} -n {nData}", timeout = 10)

    def readRegVal(self, rName):
        rAddr, rData = self.readReg(regNameRegs[f'{rName}_ADDR'])

        return rAddr,rData

    def writeRegVal(self, rName, value):
        return self.writeReg(regNameRegs[f'{rName}_ADDR'], value)

    def sendCmd(self,cmdBitPos):
        _, cmdRegVal = self.readReg(CMD_REG_ADDR)
    
        dataToWrite = ((int(CIT_PWR_MASK,16) & (1 << cmdBitPos)) | 
                       int(cmdRegVal,16))
        
        firstResp = self.writeRegVal("CMD_REG",f"{dataToWrite:08x}")
        secResp = self.writeRegVal("CMD_REG",cmdRegVal)
        
        return firstResp,secResp

    def changeConfigVal(self, valName, val, feedback=False):
        regList = []
    
        valN = valName.upper()
    
        numOfBits = valNameRegs[valN][nBits]
    
        if valN not in valNameRegs.keys():
            raise Exception(f"Errore: {valN} non presente!")

        regList.append(genRegList(valN))

        if invParamsRegex.match(valN) is None:      # controllo che il parametro da modificare non sia uno di quelli che vanno scritti LSB->MSB
            masks,vals = genMasks(valN,val)
        else:                                                   # se il parametro va scritto al contrario inverto il valore
            invertedVal = int(f"{val:0{numOfBits}b}"[::-1],2)   # converto val in binario e inverto la stringa risultante e riconverto in intero
            masks,vals = genMasks(valN,invertedVal)

        regOld = 0xFFFFFFFF

        for regs in regList:
            for i,regAddr in enumerate(regs):
                if regAddr != regOld:
                    
                    dat = vals[i]
                    msk = masks[i]
                    addrS = "{:08x}".format(regAddr)
                    
                    addrStr, dataStr = self.readReg(addrS)
                    
                    if addrStr != addrS:
                        raise Exception("Errore: indirizzi non corrispondenti!"
                                        " FromSPW={0} "
                                        "ToSPW={1}".format(addrStr,addrS))
                    
                    dataINT = int(dataStr,16)
                    
                    maskedData = dataINT & msk
                    dataToWrite = maskedData | dat
                    
                    dataToWriteStr = "{:08x}".format(dataToWrite)

                    compDataToWrite = dataToWrite & msk
                    
                    if compDataToWrite != maskedData:
                        raise Exception("Errore nella scrittura: "
                                        "maskedData={0:08x}"
                                        " compDataToWrite={1:08x}".format(maskedData,
                                                                          compDataToWrite))
                    
                    recvAddr, recvData = self.writeReg(addrS, dataToWriteStr)

                    if feedback is True:
                        print(f"@{recvAddr} = {recvData}")
                    
                    regOld = regAddr

        return regList

    def readConfigVal(self, vName):
        regList = []
        retArr = []
    
        valN = vName.upper()
        
        regList.append(genRegList(valN))
    
        masks,_ = genMasks(valN,0) # la uso solo per 
                                       # generare le maschere di registro
    
        regOld = 0xFFFFFFFF

        for regs in regList:
            retVals = []

            for i,regAddr in enumerate(regs):
                if regAddr != regOld:
                    regOld = regAddr

                    msk = masks[i] ^ 0xFFFFFFFF # nego la maschera perchè
                                                # ora devo leggere

                    addrS = f"{regAddr:08x}"
                    
                    addrStr, dataStr = self.readReg(addrS)

                    if addrStr == addrS:
                        vInt = int(dataStr,16)
                        lBP = valNameRegs[valN][lastBitL][i]
                        fBP = valNameRegs[valN][firstBitL][i]
                        retVals.append((((vInt & msk) >> lBP),(fBP-lBP+1)))

                    else:
                        raise Exception(f"Errore in lettura: "
                                        f"addrStr={addrStr} regVal={regAddr}")

            returned = ""
            for r,nB in retVals:
                returned += f"{r:0{nB}b}"

            nBits = valNameRegs[vName][4]

            retArr.append(f"{int(returned,2):0{nBits}b}")

        return retArr

    def peakDetector(self,gainLine,on,feedback=False):
        g = gainLine.upper()
        self.changeConfigVal(f"EN_{g}_TEH",int(not on),feedback=feedback)
        self.changeConfigVal(f"EN_{g}_PDET",int(on),feedback=feedback)
        self.changeConfigVal(f"SEL_SCA_OR_PEAKD_{g}",int(not on),feedback=feedback)
        self.changeConfigVal("BYPASS_PSC",int(not on),feedback=feedback)

    @_readWRegFeedback
    def powerOnCIT(self, citiroc):
        cit = citiroc.upper()
        
        if cit in CIT.keys():
            _, cmdRegVal = self.readReg(CMD_REG_ADDR)
            
            dataToWrite = int(cmdRegVal,16) | (CIT[cit] << 4)

        return self.writeRegVal("CMD_REG",f"{dataToWrite:08x}")

    @_readWRegFeedback
    def powerOffCIT(self, citiroc):
        cit = citiroc.upper()
        
        if cit in CIT.keys():
            _, cmdRegVal = self.readReg(CMD_REG_ADDR)
            
            dataToWrite = int(cmdRegVal,16) & ~(CIT[cit] << 4)

        return self.writeRegVal("CMD_REG",f"{dataToWrite:08x}")

    @_readWRegFeedback
    def applyConfiguration(self, citiroc):
        cit = citiroc.upper()
        
        if cit in CIT.keys():
            _, cmdRegVal = self.readReg(CMD_REG_ADDR)
            
            dataToWrite = ((int(CIT_PWR_MASK,16) & CIT[cit]) | 
                           int(cmdRegVal,16))
            
            return (self.writeRegVal("CMD_REG",f"{dataToWrite:08x}"),
                    self.writeRegVal("CMD_REG",cmdRegVal))

        else:
            raise Exception("Scegliere CIT0, CIT1 oppure ALL")

    def changeChargeThreshold(self, value, feedback=False):
        self.changeConfigVal("DAC_CODE_1",value,feedback=feedback)
        
    def changeTimeThreshold(self, value, feedback=False):
        self.changeConfigVal("DAC_CODE_2",value,feedback=feedback)
    
    @_readWRegFeedback
    def selectTriggerMask(self, value):
        return self.writeRegVal("TRIGGER_MASK",value)
    
    @_readWRegFeedback
    def selectGenericTriggerMask(self, value):
        return (self.writeRegVal("GENERIC_TRIGGER_MASK", value))

    @_readWRegFeedback
    def selectPMTMask(self,value,cit):
        return (self.writeRegVal(f"PMT_{cit}_MASK", value))

    @_readWRegFeedback
    def selectPrescaler(self, trgMask, prescVal):
        if type(trgMask) == int:
            if trgMask == 0:
                regToChange = "PRESC_M1_M0"
                bitMask = "FFFC0000"
                prescMasked = prescVal & int("0003FFFF",16)
            elif trgMask == 1:
                regToChange = "PRESC_M1_M0"
                bitMask = "00003FFF"
                prescMasked = (prescVal << 18)
            elif trgMask == 2:
                regToChange = "PRESC_M3_M2"
                bitMask = "FFFF0000"
                prescMasked = prescVal & int("0000FFFF",16)
            elif trgMask == 3:
                regToChange = "PRESC_M3_M2"
                bitMask = "0000FFFF"
                prescMasked = (prescVal << 16)
            else:
                raise Exception("Errore:\n\tE' possibile prescalare solo le maschere da 0 a 3!")
            
            _, prescRegVal = self.readRegVal(regToChange)

            valToWrite = (int(prescRegVal,16) & int(bitMask,16)) | prescMasked
            
            return self.writeRegVal(regToChange,f"{valToWrite:08x}")

        else:
            raise Exception("Errore:\n\ttrgMask può avere solo valori interi!")

    @_readWRegFeedback
    def flushRegisters(self):
        return self.writeRegVal("RST_REG","0DA00DA0")

    @_readCmdFeedback
    def applyTriggerMask(self):
        return self.sendCmd(APPLY_TRG_MASK)
    
    @_readCmdFeedback
    def applyPMTMask(self):
        return self.sendCmd(APPLY_PMT_MASK)

    @_readCmdFeedback
    def startACQ(self):
        return self.sendCmd(START_ACQ)

    @_readCmdFeedback
    def stopACQ(self):
        return self.sendCmd(STOP_ACQ)

    def startDPCURun(self):
        self.ssh.exec_command(f"sd/map -l 0x40c40028 =0x{regNameRegs['ACQDATALEN_ADDR']}", timeout = 10)
        self.ssh.exec_command(f"sd/map -l 0x40c4002c =0x{regNameRegs['ACQDATA0_ADDR']}", timeout = 10)
        self.ssh.exec_command("sd/map -l 0x40c40020 =0x52554E30", timeout = 10)

    def stopDPCURun(self):
        self.ssh.exec_command("sd/map -l 0x40c40020 =0x0", timeout = 10)

    def saveDataStart(self, fileName, evtNum, feedback=False):
        self.startDPCURun()

        _, stdout, _ = self.ssh.exec_command(f"sd/readevents {fileName}.dat {evtNum}", timeout = 10)

        while True:
            line = stdout.readline()
            
            if not line:
                break
            
            if feedback is True:
                print(line, end="")

    def getDataFile(self,remoteFile,localFile):
        with self.ssh.open_sftp() as sftp:
            sftp.get(f"{remoteFile}.dat",localFile)

    @_readCmdFeedback
    def startDebug(self):
        return self.sendCmd(START_DEBUG)

    @_readCmdFeedback
    def startCAL(self):
        return self.sendCmd(START_CAL)

    @_readCmdFeedback
    def stopCAL(self):
        return self.sendCmd(STOP_CAL)

    @_readCmdFeedback
    def applyPedestal(self):
        return self.sendCmd(APPLY_PEDESTALS)
    
    @_readWRegFeedback
    def changePedestal(self, dacVal, cit):
        if cit != "all":
            return (self.writeRegVal(f"REF_DAC_{CIT[cit.upper()]}",dacVal),
                    *self.applyPedestal())
    
        else:
            return (self.writeRegVal("REF_DAC_1",dacVal),
                    self.writeRegVal("REF_DAC_2",dacVal),
                    *self.applyPedestal())

    def regSnapshot(self, fileID=None):
        dataReceived = {}
        dataReceivedToFile = ""

        locTime = localtime(time())

        dateT = str(date.today())
        hours = "{:02d}".format(int(locTime[3]))
        mins = "{:02d}".format(int(locTime[4]))
        secs = "{:02d}".format(int(locTime[5]))

        timeDataStr = dateT+"-"+hours+mins+secs

        trgRegs = self.burstRead('0', '255')
        
        for i,t in enumerate(trgRegs):
            rAddr = t[0].upper()
            rVal = t[1].upper()

            if rAddr in invRegNameRegs.keys():
                regN = invRegNameRegs[rAddr].split('_ADDR')[0]
                
                dataReceived[regN] = [rAddr,rVal]
    
                dataReceivedToFile += (f"Registro {regN.ljust(20,' ')} (0x{rAddr})"
                                        f" = {rVal}\n")

        if fileID is not None:
            with open(f"REGSnapshot-{fileID}-{timeDataStr}.snap","w") as regFile:
                regFile.write(dataReceivedToFile)
        
        return dataReceived

    def close(self):
        self.ssh.close()
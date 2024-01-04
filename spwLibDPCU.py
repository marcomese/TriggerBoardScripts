# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 15:15:00 2019

@author: Marco
"""

import threading
from valNameRegs import valNameRegs
from regNameRegs import regNameRegs
from serialeLib import timeDataStr
import re

WRITE = 12
READ = 3
SPW_BYTES = 10

MSBreg = 0
LSBreg = 1
firstBitL = 2
lastBitL = 3
nBits = 4

CMD_REG_ADDR = "00000004"

GENERIC_MASK = "00000008"

triggerMasksString = {
            "T" : 0,
            "T.P1" : 1,
            "T.(P1+P2)" : 2,
            "(T3+T4).(P1+P2)" : 3,
            "T.P1.P2" : 4,
            "T.P1.P2.P3" : 5,
            "T.(P1+P2).(P15+P16)" : 6,
            "T.L" : 7
        }

triggerMasks = {
                0 : "00000000",
                1 : "00000001",
                2 : "00000002",
                3 : "00000003",
                4 : "00000004",
                5 : "00000005",
                6 : "00000006",
                7 : "00000007"
                }

CMD = {
       "write" : WRITE,
       "read" : READ
       }


ICMD = {k : v for v,k in CMD.items()}

# CIT0 <-> CITIROC A
# CIT1 <-> CITIROC B


CIT = { # valori per applyConfiguration
       "CIT0" : 1,
       "CIT1" : 2,
       "ALL"  : 3
       }

invertedParams = "TCONST_HG_SHAPER|TCONST_LG_SHAPER|DAC[0-9][0-9](?!_IN)(_T)*"

invParamsRegex = re.compile(invertedParams)

# =============================================================================
# TRIGGER BOARD PRECEDENTE:
# CIT0 <-> CITIROC B
# CIT1 <-> CITIROC A
# 
# 
# CIT = { # valori per applyConfiguration
#         "CIT1" : 1,
#         "CIT0" : 2,
#         "ALL"  : 3
#         }
# =============================================================================

probeRegs = [f"{r:08x}".upper() for r in range(0x40B,0x41B)]

probeRegsNames = {v:k for k,v in regNameRegs.items()}

probeAnalogRegs = [ar for ar in probeRegs if probeRegsNames[ar][0:7] != "PSMODEB"]

probeDigitalRegs = [dr for dr in probeRegs if dr not in probeAnalogRegs]

################ ATTENZIONE!!!! ##############################
##                                                          ##
##     Bisognerebbe modificare tutte le funzioni che        ##
##     agiscono sul registro CMD_REG_ADDR, in modo da       ##
##     tenere sempre accesi i citiroc che già lo sono       ##
##     sarebbe meglio convertire tutto in una classe.       ##
##     Per il momento modifico i valori scritti nel         ##
##     registro. In futuro cambiare tutti i valori in       ##
##     CMD_REG_ADDR nella seconda posizione.                ##
##                                                          ##
##############################################################

def applyConfiguration(ser,citiroc,feedback=False):
    cit = citiroc.upper()
    
    if cit in CIT.keys():
        writeReg(ser,CMD_REG_ADDR,f"0000003{CIT[cit]}", feedback=feedback)
        writeReg(ser,CMD_REG_ADDR,"00000030", feedback=feedback)
        readDataThread(ser, writeFeedback = True, readQueue = None) ### legge il feedback dallo 
                                                                    ### spacewire altrimenti resta nella fifo
    else:
        raise Exception("Scegliere CIT0, CIT1 oppure ALL")

def sendCmd(ser,cmd,addr,data="00000000", feedback = False):
    addrUnpacked = []
    dataUnpacked = []
    
    addrLen = len(addr)
    dataLen = len(data)
    
    if addrLen > 8:
        raise Exception("Gli indirizzi devono essere a 32 bit!")
    elif dataLen > 8:
        raise Exception("I dati devono essere a 32 bit!")
    
    for i in range(0,addrLen,2):
        addrUnpacked.append(int(addr[i:i+2],16))
    for i in range(0,dataLen,2):
        dataUnpacked.append(int(data[i:i+2],16))
    
    addrUnpacked.reverse()
    dataUnpacked.reverse()
    
    c = bytes([cmd,*tuple(addrUnpacked),*tuple(dataUnpacked),0])
    ser.write(c)
    
    tupC = tuple(c)
    
    if feedback is True:
        cStr, _, _ = fromSPWToString(tupC)
        print("Inviato:\t{}".format(cStr))
    
    return tupC

def readData(ser): #tu sei malato
    while True:    #togli questa roba e fai le cose normali: ser.read(SPW_BYTES) e timeout impostato
#        if ser.in_waiting > 0:
        if ser.in_waiting == SPW_BYTES:
            #readStr = tuple(ser.read(SPW_BYTES))
            readStr = tuple(ser.read(ser.in_waiting))
            break

    return tuple(readStr)

def fromSPWToString(spwAns):
    addrStr = ""
    dataStr = ""
    readStrHex = ""

    for d in spwAns[4:0:-1]:
        addrStr += "{:02x}".format(d)
    for d in spwAns[8:4:-1]:
        dataStr += "{:02x}".format(d)        
    
        readStrHex = "CMD = {} ADDR = 0x{} DATA = 0x{}".format(ICMD[spwAns[0]],
                                                            addrStr.upper(),
                                                            dataStr.upper())
    return readStrHex,addrStr,dataStr

def readReg(ser,regAddr, feedback = False): # deve essere seguito da un readData
    return sendCmd(ser,READ,regAddr,feedback = feedback)

def writeReg(ser,regAddr,data, feedback = False):
    return sendCmd(ser,WRITE,regAddr,data,feedback = feedback)

def startReadingThread(ser, writeFeedback = False, readQueue = None):
    readSerialTh = threading.Thread(target = readDataThread,
                                    name = "readSerialThread",
                                    args = (ser, writeFeedback, readQueue))
    readSerialTh.start()
    return readSerialTh

def stopReadingThread(th):
    th.join()

#### CORREGGERE IL BUG CHE SI HA QUANDO SI IMPOSTA writeFeedback = False
def readDataThread(ser, writeFeedback, readQueue): # trovare il modo di
    while True:                                    # richiamarla di nuovo
        if ser.in_waiting > 0:
            
            readVal = tuple(ser.read(SPW_BYTES))
            
            if readQueue is not None:
                readQueue.put(readVal)
                
            if writeFeedback is False and readVal[0] == WRITE:
                continue
            
            readStr, _, _= fromSPWToString(readVal)
            print("Ricevuto:\t{}".format(readStr))
            if ser.in_waiting == 0:
                break

def genRegList(valN,citIndex):
    regList = (
            valNameRegs[valN][MSBreg] + (citIndex * 0x24),
            valNameRegs[valN][LSBreg] + (citIndex * 0x24),
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

def changeConfigVal(ser,valName,val,citiroc, feedback = True):
    regList = []

    cit = citiroc.upper()
    valN = valName.upper()

    numOfBits = valNameRegs[valN][nBits]

    if cit not in CIT.keys():
        raise Exception("Errore: {} non presente!".format(cit))
    elif valN not in valNameRegs.keys():
        raise Exception("Errore: {} non presente!".format(valN))
    else: 
        citIndex = CIT[cit]-1
    
        if(cit == "ALL"):
            for i in range(citIndex):
                regList.append(genRegList(valN,i))
        else:
            regList.append(genRegList(valN,citIndex))

        if invParamsRegex.match(valN) is None:      # controllo che il parametro da modificare non sia uno di quelli che vanno scritti LSB->MSB
            masks,vals = genMasks(valN,val)
        else:                                       # se il parametro va scritto al contrario inverto il valore
            invertedVal = int(f"{val:0{numOfBits}b}"[::-1],2)   # converto val in binario e inverto la stringa risultante e riconverto in intero
            masks,vals = genMasks(valN,invertedVal)

        regOld = 0xFFFFFFFF
        
        ser.reset_input_buffer()
        ser.reset_output_buffer() # svuota i buffer per evitare di lasciare
                                   # dati precedenti nella fifo
        for regs in regList:
            for i,regAddr in enumerate(regs):
                if regAddr != regOld:
                    
                    dat = vals[i]
                    msk = masks[i]
                    addrS = "{:08x}".format(regAddr)
                    
                    readReg(ser,addrS,feedback = True)
                    spwData = readData(ser)
                    _, addrStr, dataStr = fromSPWToString(spwData)
                    
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
                    
                    writeReg(ser,addrS,dataToWriteStr,feedback = feedback)

                    receivedSPW = readData(ser)                  ### legge il feedback dallo 
                    recvStr, _, _ = fromSPWToString(receivedSPW) ### spacewire altrimenti resta nella fifo
                    if feedback is True:
                        print("Ricevuto:\t{}".format(recvStr))
                    
                    regOld = regAddr

    return regList

def changeProbeRegVal(ser,valName,val,feedback = True):

    valN = valName.upper()

    if valN not in regNameRegs.keys():
        raise Exception("Errore: {} non presente!".format(valN))
    elif regNameRegs[valN] not in probeRegs:
        raise Exception(f"Errore: {valN} non è un registro di probe!")

    ser.reset_input_buffer()
    ser.reset_output_buffer() # svuota i buffer per evitare di lasciare
                               # dati precedenti nella fifo

    reg = regNameRegs[valN]

    isAnalog = reg in probeAnalogRegs
    
    readReg(ser,reg,feedback = True)
    spwData = readData(ser)
    _, addrStr, dataStr = fromSPWToString(spwData)
    
    if addrStr != reg.lower():
        raise Exception("Errore: indirizzi non corrispondenti!"
                        " FromSPW={0} "
                        "ToSPW={1}".format(addrStr,reg))
    
    if isAnalog is True:
        for r in probeAnalogRegs:
            print(f"Azzero il registro {probeRegsNames[r]}...")
            writeReg(ser,r,"00000000",feedback = feedback) # per evitare che vengano impostate sul probe più di una uscita
            citiroc = "cit1" if int(r,16) >= 1042 else "cit0"
            applyConfiguration(ser,citiroc,feedback=False)
    else:
        for r in probeDigitalRegs:
            print(f"Azzero il registro {probeRegsNames[r]}...")
            writeReg(ser,r,"00000000",feedback = feedback) # per evitare che vengano impostate sul probe più di una uscita
            citiroc = "cit1" if int(r,16) >= 1042 else "cit0"
            applyConfiguration(ser,citiroc,feedback=False)

    writeReg(ser,reg,val,feedback = feedback)

    _ = ser.read(ser.in_waiting)       ### legge il feedback dallo 
                                       ### spacewire altrimenti resta nella fifo

    citiroc = "cit1" if int(reg,16) >= 1042 else "cit0"

    print(f"Abilito l'uscita di probe a {citiroc.upper()}")
    applyConfiguration(ser,citiroc,feedback=False)

    return reg

def peakDetector(spwSer,gainLine,on,cit):
    g = gainLine.upper()
    changeConfigVal(spwSer,f"EN_{g}_TEH",int(not on),cit)
    changeConfigVal(spwSer,f"EN_{g}_PDET",int(on),cit)
    changeConfigVal(spwSer,f"SEL_SCA_OR_PEAKD_{g}",int(not on),cit)
    changeConfigVal(spwSer,"BYPASS_PSC",int(not on),cit)

def readConfigVal(ser,vName,citiroc):
    regList = []
    retArr = []

    valN = vName.upper()
    
    cit = citiroc.upper()
    
    if cit not in CIT.keys():
        raise Exception("Errore: {} non presente!".format(cit))
    elif valN not in valNameRegs.keys():
        raise Exception("Errore: {} non presente!".format(valN))
    else: 
        citIndex = CIT[cit]-1
    
        if(cit == "ALL"):
            for i in range(citIndex):
                regList.append(genRegList(valN,i))
        else:
            regList.append(genRegList(valN,citIndex))

        masks,_ = genMasks(valN,0)# la uso solo per 
                                   # generare le maschere di registro

        regOld = 0xFFFFFFFF
        
        ser.reset_input_buffer()
        ser.reset_output_buffer() # svuota i buffer per evitare di lasciare
                                   # dati precedenti nella fifo

        for regs in regList:
            retVals = []

            for i,regAddr in enumerate(regs):
                if regAddr != regOld:
                    regOld = regAddr

                    msk = masks[i] ^ 0xFFFFFFFF # nego la maschera perchè
                                                # ora devo leggere

                    addrS = f"{regAddr:08x}"
                    
                    readReg(ser,addrS,feedback = True)
                    spwData = readData(ser)
                    _, addrStr, dataStr = fromSPWToString(spwData)

                    if addrStr == addrS:
                        vInt = int(dataStr,16)
                        lBP =  valNameRegs[valN][lastBitL][i]
                        retVals.append((vInt & msk) >> lBP)

                    else:
                        raise Exception("Errore in lettura: "
                                        "addrStr={} regVal={}".format(addrStr,
                                                                      regAddr))
            returned = ""
            for r in retVals:
                returned += f"{r:b}"
            
            nBits = valNameRegs[vName][4]

            retArr.append(f"{int(returned,2):0{nBits}b}")

        return retArr

def readRegVal(ser,rName):
    rAddr = regNameRegs[f'{rName}_ADDR']

    readReg(ser,regNameRegs[f'{rName}_ADDR'])
    rVal = fromSPWToString(readData(ser))[0].split('DATA = ')[1]

    return rAddr,rVal

def changeChargeThreshold(ser,cit,value):
    changeConfigVal(ser,"DAC_CODE_1",value,cit)
    
def changeTimeThreshold(ser,cit,value):
    changeConfigVal(ser,"DAC_CODE_2",value,cit)

def selectTriggerMask(ser,value,feedback=False):
    if type(value) is int and value in triggerMasks.keys():
            writeReg(ser,regNameRegs["TRIGGER_MASK_ADDR"],
                     triggerMasks[value],
                     feedback = feedback)
            readDataThread(ser, writeFeedback = True, readQueue = None) ### legge il feedback dallo 
                                                                            ### spacewire altrimenti resta nella fifo
    elif type(value) is str:
            print(f"Seleziono la trigger mask: {value}")
            writeReg(ser,regNameRegs["TRIGGER_MASK_ADDR"],
                     value,
                     feedback = feedback)
            readDataThread(ser, writeFeedback = True, readQueue = None) ### legge il feedback dallo 
                                                                            ### spacewire altrimenti resta nella fifo
    else:
        raise Exception(f"Errore! {value} non riconosciuto!")

def changeGenericTriggerMask(ser,value,feedback=False):
    writeReg(ser,regNameRegs["TRIGGER_MASK_ADDR"], GENERIC_MASK,
             feedback = feedback)
    writeReg(ser,regNameRegs["GENERIC_TRIGGER_MASK_ADDR"],
             value,feedback = feedback)

    readDataThread(ser, writeFeedback = True, readQueue = None) ### legge il feedback dallo 
                                                                    ### spacewire altrimenti resta nella fifo

def applyTriggerMask(ser,feedback=False):
    writeReg(ser,regNameRegs["CMD_REG_ADDR"],"000000B0")
    writeReg(ser,regNameRegs["CMD_REG_ADDR"],"00000030")
    readDataThread(ser, writeFeedback = True, readQueue = None) ### legge il feedback dallo 
                                                                    ### spacewire altrimenti resta nella fifo

def applyPMTMask(ser,feedback=False):
    writeReg(ser,regNameRegs["CMD_REG_ADDR"],"00000130")
    writeReg(ser,regNameRegs["CMD_REG_ADDR"],"00000030")
    readDataThread(ser, writeFeedback = True, readQueue = None) ### legge il feedback dallo 
                                                                    ### spacewire altrimenti resta nella fifo

def startACQ(ser):
    writeReg(ser,regNameRegs["CMD_REG_ADDR"],"00000230")
    writeReg(ser,regNameRegs["CMD_REG_ADDR"],"00000030")
    readDataThread(ser, writeFeedback = True, readQueue = None) ### legge il feedback dallo 
                                                                    ### spacewire altrimenti resta nella fifo

def stopACQ(ser):
    writeReg(ser,regNameRegs["CMD_REG_ADDR"],"00000430")
    writeReg(ser,regNameRegs["CMD_REG_ADDR"],"00000030")
    readDataThread(ser, writeFeedback = True, readQueue = None) ### legge il feedback dallo 
                                                                    ### spacewire altrimenti resta nella fifo

def startDebug(ser):
    writeReg(ser,regNameRegs["CMD_REG_ADDR"],"00000070")
    writeReg(ser,regNameRegs["CMD_REG_ADDR"],"00000030")
    readDataThread(ser, writeFeedback = True, readQueue = None) ### legge il feedback dallo 
                                                                    ### spacewire altrimenti resta nella fifo

def startCAL(ser):
    writeReg(ser,regNameRegs["CMD_REG_ADDR"],"00000830")
    writeReg(ser,regNameRegs["CMD_REG_ADDR"],"00000030")
    readDataThread(ser, writeFeedback = True, readQueue = None) ### legge il feedback dallo 
                                                                    ### spacewire altrimenti resta nella fifo

def stopCAL(ser):
    writeReg(ser,regNameRegs["CMD_REG_ADDR"],"00001030")
    writeReg(ser,regNameRegs["CMD_REG_ADDR"],"00000030")
    readDataThread(ser, writeFeedback = True, readQueue = None) ### legge il feedback dallo 
                                                                    ### spacewire altrimenti resta nella fifo
def startReaders(ser):
    writeReg(ser,regNameRegs["CMD_REG_ADDR"],"00000034")
    writeReg(ser,regNameRegs["CMD_REG_ADDR"],"00000030")
    readDataThread(ser, writeFeedback = True, readQueue = None) ### legge il feedback dallo 
                                                                ### spacewire altrimenti resta nella fifo                             
def initPedestal(ser):
    writeReg(ser,regNameRegs["CMD_REG_ADDR"],"00004030")
    writeReg(ser,regNameRegs["CMD_REG_ADDR"],"00000030")
    readDataThread(ser, writeFeedback = True, readQueue = None) ### legge il feedback dallo 
                                                                    ### spacewire altrimenti resta nella fifo
    
def changePedestal(ser, dacVal, cit):
    if cit != "all":
        writeReg(ser,regNameRegs[f"REF_DAC_{CIT[cit.upper()]}_ADDR"],dacVal)
        writeReg(ser,regNameRegs["CMD_REG_ADDR"],"00004030")
        writeReg(ser,regNameRegs["CMD_REG_ADDR"],"00000030")
        readDataThread(ser, writeFeedback = True, readQueue = None) ### legge il feedback dallo 
                                                                    ### spacewire altrimenti resta nella fifo
    else:
        writeReg(ser,regNameRegs[f"REF_DAC_1_ADDR"],dacVal)
        writeReg(ser,regNameRegs["CMD_REG_ADDR"],"00004030")
        writeReg(ser,regNameRegs["CMD_REG_ADDR"],"00000030")
        writeReg(ser,regNameRegs[f"REF_DAC_2_ADDR"],dacVal)
        writeReg(ser,regNameRegs["CMD_REG_ADDR"],"00004030")
        writeReg(ser,regNameRegs["CMD_REG_ADDR"],"00000030")
        readDataThread(ser, writeFeedback = True, readQueue = None)

def powerOnCIT(ser,cit):
    writeReg(ser,regNameRegs["CMD_REG_ADDR"],f"000000{CIT[cit.upper()]}0")
    readDataThread(ser, writeFeedback = True, readQueue = None) ### legge il feedback dallo 
                                                                    ### spacewire altrimenti resta nella fifo

def powerOffCITs(ser):
    writeReg(ser,regNameRegs["CMD_REG_ADDR"],"00000000")
    readDataThread(ser, writeFeedback = True, readQueue = None) ### legge il feedback dallo 
                                                                    ### spacewire altrimenti resta nella fifo


def regSnapshot(ser,fileName=None,latexTAB = False):
    dataReceived = {}
    dataReceivedToFile = ""

    for rName,rAddr in regNameRegs.items():
        regN = rName.split('_ADDR')[0]
        readReg(ser,regNameRegs[rName])
        rVal = fromSPWToString(readData(ser))[0].split('DATA = ')[1]
        
        dataReceived[regN] = [rAddr, rVal]
        
        dataReceivedToFile += (f"Registro {regN.ljust(20,' ')} (0x{rAddr})"
                               f" = {rVal}\n")

    if fileName is not None:
        with open(f"REGSnapshot-{fileName}-{timeDataStr}.snap","w") as regFile:
            regFile.write(dataReceivedToFile)
    
    return dataReceived

#    if latexTAB is True:
#        with open(f"REGSnapshot-{fileName}-{timeDataStr}.tex","w") as regFile:
#            regFile.write("\\begin{table}\n"
#                          "\\centering\n"
#                          "\\begin{tabular}{c c}\n"
#                          "\\toprule\n"
#                          "REGISTRO & VALORE\\tabularnewline\n"
#                          "\\midrule\n")
#
#            for rName,rAddr in regNameRegs.items():
#                regN = rName.split('_ADDR')[0]
#                readReg(ser,regNameRegs[rName])
#                rVal = fromSPWToString(readData(ser))[0].split('DATA = ')[1]
#                regFile.write(f"{regN.ljust(20,' ')} & {rVal}\\tabularnewline\n")
#            
#            regFile.write("\\bottomrule\n"
#                          "\\end{tabular}\n"
#                          "\\end{table}\n")
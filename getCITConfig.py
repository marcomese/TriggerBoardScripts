# -*- coding: utf-8 -*-
"""
Created on Mon Nov 28 16:00:27 2022

@author: limadou
"""

import re
from valNameRegs import valNameRegs
from regNameRegs import regNameRegs
import citSupportLib as csl
from gainsConfig import gainsConfig as gConf

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

citConf = gConf.copy()

defGains = {
        'ch00': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
        'ch01': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
        'ch02': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
        'ch03': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
        'ch04': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
        'ch05': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
        'ch06': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
        'ch07': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
        'ch08': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
        'ch09': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
        'ch10': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
        'ch11': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
        'ch12': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
        'ch13': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
        'ch14': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
        'ch15': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
        'ch16': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
        'ch17': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
        'ch18': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
        'ch19': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
        'ch20': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
        'ch21': {'hg': 10.0, 'lg': 1.5, 'inCalib': None, 'enabled': True},
        'ch22': {'hg': 10.0, 'lg': 1.5, 'inCalib': None, 'enabled': True},
        'ch23': {'hg': 10.0, 'lg': 1.5, 'inCalib': None, 'enabled': True},
        'ch24': {'hg': 10.0, 'lg': 1.5, 'inCalib': None, 'enabled': True},
        'ch25': {'hg': 10.0, 'lg': 1.5, 'inCalib': None, 'enabled': True},
        'ch26': {'hg': 10.0, 'lg': 1.5, 'inCalib': None, 'enabled': True},
        'ch27': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
        'ch28': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
        'ch29': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
        'ch30': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
        'ch31': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
    }

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

def changeConfigVal(valName, val, defVals = True):
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
                
                addrS = "{:08x}".format(regAddr).upper()
                
                if defVals is True:
                    dataStr = citConf[addrS]
                else:
                    dataStr = "00000000"
                
                dat = vals[i]
                msk = masks[i]

                dataINT = int(dataStr,16)
                
                maskedData = dataINT & msk
                dataToWrite = maskedData | dat
                
                dataToWriteStr = "{:08x}".format(dataToWrite)

                citConf[addrS] = dataToWriteStr
                
                regOld = regAddr

    return citConf

def getGain(gains, defVals = True):
    for c,g in gains.items():
        regGain = csl.getGainStr(g['hg'],
                                 g['lg'],
                                 g['inCalib'],
                                 g['enabled'])

        return changeConfigVal(f"PREAMP_CONFIG{csl.chToNum[c]}",
                               int(regGain,2),defVals)

def getConf(thresholds, gains, defVals = True):
    retDict = {}

    changeConfigVal("DAC_CODE_1",thresholds['charge'],defVals)
    changeConfigVal("DAC_CODE_2",thresholds['time'],defVals)

    for c,g in gains.items():
        regGain = csl.getGainStr(g['hg'],
                                 g['lg'],
                                 g['inCalib'],
                                 g['enabled'])

        retDict = changeConfigVal(f"PREAMP_CONFIG{csl.chToNum[c]}",
                                  int(regGain,2),defVals)
    
    return retDict

# def genTas(tasName, thresholds, gains, delay=10):
#     getConf(thresholds, gains)
    
#     with open(f"{tasName}.tas","w") as tasFile:
#         for k,v in citConf.items():
#             if Conf[k] != v.upper():
#                 tasFile.write(f"W 3 0x{k} 0x{v.upper()}\n")
#                 tasFile.write(f"S {delay}\n")
        
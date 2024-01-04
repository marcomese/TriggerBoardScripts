# -*- coding: utf-8 -*-

from valNameRegs import valNameRegs as valRegs
from regNameRegs import regNameRegs as regs
from copy import deepcopy
from datetime import date
from time import localtime,time
from itertools import chain
import numpy as np


dateT = date.today().strftime("%d-%m-%y")
hours = f"{int(localtime(time())[3]):02d}"
mins = f"{int(localtime(time())[4]):02d}"
secs = f"{int(localtime(time())[5]):02d}"

timeDataStr = f"{dateT}-{hours}{mins}{secs}"

citToReg = {'cit0':1,'cit1':2}
hglgToVal = {'hg' : 0, 'lg' : 1}
invHGLGToVal = {v:k for k,v in hglgToVal.items()}
chToNum = {f"ch{i:02d}":f"{i:02d}" for i in range(0,32)}
inCalibHGLG = {'hg' : "10", 'lg' : "01", None : "00"}
invInCalibHGLG = {v:k for k,v in inCalibHGLG.items()}
feedbackCaps = [fCap for fCap in range(1575,0,-25)]
typDACToReg = {"charge" : "dac_code_1",
               "time" : "dac_code_2"}

gainBitsToHGGain = {f"{bits:06b}" : round(15000/cap,3) for bits,cap in enumerate(feedbackCaps)}
gainBitsToLGGain = {f"{bits:06b}" : round(1500/cap,3) for bits,cap in enumerate(feedbackCaps)}
gainBitsToInCALIBGain = {f"{bits:06b}" : round(3000/cap,3) for bits,cap in enumerate(feedbackCaps)}

HGGainToGainBits = {v : k for k,v in gainBitsToHGGain.items()}
LGGainToGainBits = {v : k for k,v in gainBitsToLGGain.items()}
InCALIBGainToGainBits = {v : k for k,v in gainBitsToInCALIBGain.items()}

HGValidGains = list(HGGainToGainBits.keys())
LGValidGains = list(LGGainToGainBits.keys())
InCALIBValidGains = list(InCALIBGainToGainBits.keys())

hglgToGainBitsDict = {'hg' : HGGainToGainBits,
                      'lg' : LGGainToGainBits}

hglgToValidGainDict = {'hg' : HGValidGains,
                       'lg' : LGValidGains}

tConstShaperBitToTConst = {f"{i:03b}"[::-1]:87.5-12.5*i for i in range(7)}

tConstShaperBitRev = {f"{i:03b}":87.5-12.5*i for i in range(7)}

tConstShaperToID = {v:int(k,2) for k,v in tConstShaperBitRev.items()}

oddMasks = int.from_bytes(0xFFF000.to_bytes(3,'big') * 64, 'big')
evenMasks = int.from_bytes(0x000FFF.to_bytes(3,'big') * 64, 'big')

GAIN = {'HG':0, 'LG':1}
CIT = {'CIT0':0, 'CIT1':1}

probeNameToReg = {"OUTFS":"OUTFS_{0}_ADDR",
                  "OUTSSH":"OUTSSH{1}_{0}_ADDR",
                  "PSMODEB":"PSMODEB{1}_{0}_ADDR",
                  "OUTSSH":"OUTSSH{1}_{0}_ADDR",
                  "OUTPA":"OUTPA{1}_{0}_ADDR",
                  "INPUTDAC":"INPUTDAC_{0}_ADDR"}

def nearestTo(val,valList):
    centersList = []
    valL = valList.copy()
    valL.sort()
    
    if val < valL[0]:
        return valL[0]
    elif val > valL[-1]:
        return valL[-1]
    else:
        valLLen = len(valL)
        
        for i in range(1,valLLen):
            centersList.append(valL[i-1]+(valL[i]-valL[i-1])/2)
    
        for i,v in enumerate(valL):
            retVal = v
            if i == len(centersList):
                break
            elif val > centersList[i]:
                continue
            else:
                break

    return retVal

def getGainBits(valGain,gainDict,validGains):
    if valGain in gainDict:
        gainBits = gainDict[valGain]
    else:
        nearestGain = nearestTo(valGain,validGains)
        gainBits = gainDict[nearestGain]
        print(f"{valGain} non impostabile, imposto il guadagno "
              f"al valore più vicino: {nearestGain}")
    
    return gainBits

def getGainStr(hgGain,lgGain,inCalib,enabled):
    if inCalib is None:
        hgBits = getGainBits(hgGain,HGGainToGainBits,HGValidGains)
        lgBits = getGainBits(lgGain,LGGainToGainBits,LGValidGains)
    elif inCalib == "hg":
        hgBits = getGainBits(hgGain,InCALIBGainToGainBits,InCALIBValidGains)
        lgBits = getGainBits(lgGain,LGGainToGainBits,LGValidGains)
    elif inCalib == "lg":
        hgBits = getGainBits(hgGain,HGGainToGainBits,HGValidGains)
        lgBits = getGainBits(lgGain,InCALIBGainToGainBits,InCALIBValidGains)
    else:
        raise ValueError("Errore! Possibili valori per 'inCalib': hg|lg|None")
    
    inCalibStr = inCalibHGLG[inCalib]
    enStr = int(not enabled)
    lastBits = f"{inCalibStr}{enStr}"
    
    return f"{hgBits}{lgBits}{lastBits}"

def getCITConfiguration(tbRegs):
    citRegs = {}

    citConf = {}

    for i in range(36):
        tr = tbRegs[f'CONFIG_CITIROC_1_{i}']

        trk = int(tr[0],16)

        citRegs[trk] = f"{int(tr[1],16):032b}"

    for k,v in valRegs.items():
        reg0 = v[0]
        reg1 = v[1]

        bit0Reg0 = 31-v[2][0]    # la stringa di testo prende il MSB come indice 0,
        bit0Reg1 = 31-v[2][-1]   # quindi seleziono i bit per far sì che 0 -> LSB
        bit1Reg0 = 31-v[3][0]+1  # aggiungo 1 perchè lo slicing degli array esclude
        bit1Reg1 = 31-v[3][-1]+1 # l'ultimo elemento

        if reg0 == reg1:
            citConf[k] = f"{citRegs[reg0][bit0Reg0:bit1Reg0]}"

        else:
            citConf[k] = (f"{citRegs[reg0][bit0Reg0:bit1Reg0]}"
                          f"{citRegs[reg1][bit0Reg1:bit1Reg1]}")

    return citConf

def citBinaryToVal(citReg,citBinVal):
    if citReg[:-2] == 'PREAMP_CONFIG':
        if citBinVal[12] == '1' and citBinVal[13] == '0':
            inCalibVal = 'hg'
            hgGainVal = gainBitsToInCALIBGain[citBinVal[0:6]]
            lgGainVal = gainBitsToLGGain[citBinVal[6:12]]
        elif citBinVal[12] == '0' and citBinVal[13] == '1':
            inCalibVal = 'lg'
            hgGainVal = gainBitsToHGGain[citBinVal[0:6]]
            lgGainVal = gainBitsToInCALIBGain[citBinVal[6:12]]
        elif citBinVal[12] == '1' and citBinVal[13] == '1':
            inCalibVal = 'hglg' # gli ingressi di calibrazione non dovrebbero essere abilitati entrambi!
            hgGainVal = gainBitsToInCALIBGain[citBinVal[0:6]]
            lgGainVal = gainBitsToInCALIBGain[citBinVal[6:12]]
        else:
            inCalibVal = None
            hgGainVal = gainBitsToHGGain[citBinVal[0:6]]
            lgGainVal = gainBitsToLGGain[citBinVal[6:12]]


        retVal = {'hg':hgGainVal,
                  'lg':lgGainVal,
                  'inCalib':inCalibVal,
                  'enabled':bool(citBinVal[14])}

    elif citReg[:6] == 'TCONST':
        retVal = tConstShaperBitToTConst[citBinVal]

    elif citReg == 'DISCRI_MASK':
        retVal = citBinVal

    else:
        retVal = int(citBinVal,2)
    
    return retVal

def citConfToValues(citRegs):
    citRegOut = deepcopy(citRegs)

    for reg,val in citRegs.items():
        citRegOut[reg] = citBinaryToVal(reg,val)

    return citRegOut

def getPacketsFromRawFile(dataFileName,bigEndianData=True):
    dataFile = open(dataFileName,'rb')

    if bigEndianData is True:
        startWord = b'FE'
        stopWord = b'GH'
    else:
        startWord = b'EF'
        stopWord = b'HG'

    startWordLen = len(startWord)
    stopWordLen = len(stopWord)
    
    data = dataFile.read()
    
    dataFile.close()
    
    packets = []
    trgCounterLen = 4
    ppsCounterLen = 4
    trgIDLen = 1
    adcLen = 192
    lostLen = 2
    aliveLen = 4
    deadLen = 4
    trgFlag1Len = 4
    trgFlag2Len = 4
    turrFlagLen = 1
    turrCntLen = 20
    dataPacketLen = 244

    for i,d in enumerate(data):
        iStw = i+startWordLen
        iEvtN = iStw+trgCounterLen
        iPPS = iEvtN+ppsCounterLen
        iTRGID = iPPS+trgIDLen
        iADC = iTRGID+adcLen
        iLost = iADC+lostLen
        iAlive = iLost+aliveLen
        iDead = iAlive+deadLen
        iTrgFlg1 = iDead+trgFlag1Len
        iTrgFlg2 = iTrgFlg1+trgFlag2Len
        iTurrFlg = iTrgFlg2+turrFlagLen
        iTurrCnt = iTurrFlg+turrCntLen
        iEnd = i+startWordLen+dataPacketLen
        iEndW = i+startWordLen+dataPacketLen+stopWordLen

        if (data[i:iStw] == startWord and data[iEnd:iEndW] == stopWord):
            packets.append({'trgCount'     : data[iStw:iEvtN],
                            'ppsCount'     : data[iEvtN:iPPS],
                            'trgID'        : data[iPPS:iTRGID],
                            'adcs'         : data[iTRGID:iADC],
                            'lostTrgCount' : data[iADC:iLost],
                            'aliveTime'    : data[iLost:iAlive],
                            'deadTime'     : data[iAlive:iDead],
                            'trgFlag1'     : data[iDead:iTrgFlg1],
                            'trgFlag2'     : data[iTrgFlg1:iTrgFlg2],
                            'turrFlag'     : data[iTrgFlg2:iTurrFlg],
                            'turrCnt'      : data[iTurrFlg:iTurrCnt],
                            'crc32'        : data[iTurrCnt:iEnd]})

    return packets

def getADCsFromPackets(packets,bigEndianData=True):
    adcBytes = 192
    nCit=2
    gains=2
    channels=32
    
    adcVals = np.zeros((nCit*gains*channels,len(packets)))
    
    auxData = []
    
    for i,p in enumerate(packets):
        if bigEndianData is True:
            pAdcs = int.from_bytes(p['adcs'],'big')

        else:
            pAdcs = int.from_bytes(p['adcs'][::-1],'big')

        packetHighData = (pAdcs & oddMasks).to_bytes(adcBytes,'big')
        packetLowData = (pAdcs & evenMasks).to_bytes(adcBytes,'big')

        oddChVals = [packetHighData[i] << 4 | packetHighData[i+1] >> 4
                     for i in range(len(packetHighData)) if i % 3 == 0]
    
        evenChVals = [packetLowData[i+1] << 8 | packetLowData[i+2]
                      for i in range(len(packetLowData)-1) if i % 3 == 0]

        adcVals[::-1,i] = list(chain(*zip(oddChVals,evenChVals)))
        
        auxData.append({"trgCount"     : int.from_bytes(p['trgCount'],'big'),
                        "ppsCount"     : (int.from_bytes(p['ppsCount'][0:2],'big'),
                                          int.from_bytes(p['ppsCount'][2:4],'big')*16), #gli ultimi 16 bit sono contati ogni 16 us
                        "trgID"        : f"{int.from_bytes(p['trgID'],'big'):08b}",
                        "lostTrgCount" : int.from_bytes(p['lostTrgCount'],'big'),
                        "aliveTime"    : int.from_bytes(p['aliveTime'],'big')*5,
                        "deadTime"     : (int.from_bytes(p['deadTime'],'big')+1)*5,
                        "trgFlagCIT0"  : f"{int.from_bytes(p['trgFlag1'],'big'):032b}",
                        "trgFlagCIT1"  : f"{int.from_bytes(p['trgFlag2'],'big'):032b}",
                        "turrFlag"     : f"{int.from_bytes(p['turrFlag'],'big'):05b}",
                        "turr0Cnt"     : int.from_bytes(p['turrCnt'][16:20],'big'),
                        "turr1Cnt"     : int.from_bytes(p['turrCnt'][12:16],'big'),
                        "turr2Cnt"     : int.from_bytes(p['turrCnt'][8:12],'big'),
                        "turr3Cnt"     : int.from_bytes(p['turrCnt'][4:8],'big'),
                        "turr4Cnt"     : int.from_bytes(p['turrCnt'][0:4],'big'),
                        "crc32"        : int.from_bytes(p['crc32'],'big')})

    return adcVals,auxData

def makeCITDict(dataIn,auxDataIn=None,stdDev=None,nevtMeans=None,rec=False):
    c0hgOff = 96
    c0lgOff = 64
    c1hgOff = 32

    data = dataIn

    if stdDev is None:
        if rec is False:
            auxData = auxDataIn
            nEvt = len(data.T)
    
            citDict = {'cit0':{f'ch{i:02d}':{'hg': data[i+c0hgOff],
                                             'lg': data[i+c0lgOff]}
                               for i in range(32)},
                       'cit1':{f'ch{i:02d}':{'hg': data[i+c1hgOff],
                                             'lg': data[i]}
                               for i in range(32)},
                       'nEvt':nEvt,
                       'auxData':auxData}
        else:
            auxData = auxDataIn
            nEvt = len(data.T)
    
            citDict = {'cit0':{f'ch{i:02d}':{'hg': data[i],
                                             'lg': data[i+32]}
                               for i in range(32)},
                       'cit1':{f'ch{i:02d}':{'hg': data[i+64],
                                             'lg': data[i+96]}
                               for i in range(32)},
                       'nEvt':nEvt,
                       'auxData':auxData}
    else:
        citDict =  {'cit0':{f'ch{i:02d}':{'hg':{'mean':data[i],
                                                'stddev':stdDev[i]},
                                          'lg':{'mean':data[i+32],
                                                'stddev':stdDev[i+32]}}
                            for i in range(32)},
                    'cit1':{f'ch{i:02d}':{'hg':{'mean':data[i+64],
                                                'stddev':stdDev[i+64]},
                                          'lg':{'mean':data[i+96],
                                                'stddev':stdDev[i+96]}}
                            for i in range(32)}}
        
        if nevtMeans is not None:
            citDict.update({'nEvt':nevtMeans})
    # if stdDev is None:
    #     citDict = {'cit0':{f'ch{i:02d}':{'hg': data[i+c0hgOff],
    #                                       'lg': data[i+c0lgOff]}
    #                         for i in range(32)},
    #                 'cit1':{f'ch{i:02d}':{'hg': data[i+c1hgOff],
    #                                       'lg': data[i]}
    #                         for i in range(32)},
    #                 'nEvt':nEvt,
    #                 'auxData':auxData}
    # else:
    #     citDict =  {'cit0':{f'ch{i:02d}':{'hg':{'mean'   : np.mean(data[i+c0hgOff]),
    #                                             'stddev' : np.std(data[i+c0hgOff])},
    #                                       'lg':{'mean'   : np.mean(data[i+c0lgOff]),
    #                                             'stddev' : np.std(data[i+c0lgOff])}}
    #                         for i in range(32)},
    #                 'cit1':{f'ch{i:02d}':{'hg':{'mean'   : data[i+c1hgOff],
    #                                             'stddev' : stdDev[i+c1hgOff]},
    #                                       'lg':{'mean'   : data[i],
    #                                             'stddev' : stdDev[i+c1lgOff]}}
    #                         for i in range(32)},
    #                 'nEvt':nEvt,
    #                 'auxData':auxData}

    return citDict

def fileChWrite(vals):
    cit0HGStr = ' '.join(str(int(a)).ljust(6,' ')
                         for a in vals[0:32])
    cit0LGStr = ' '.join(str(int(a)).ljust(6,' ')
                            for a in vals[32:64])
    cit1HGStr = ' '.join(str(int(a)).ljust(6,' ')
                            for a in vals[64:96])
    cit1LGStr = ' '.join(str(int(a)).ljust(6,' ')
                            for a in vals[96:128])
    return (f"{cit0HGStr} "
            f"{cit0LGStr} "
            f"{cit1HGStr} "
            f"{cit1LGStr}\n")

def makeTabFile(fileName,citDict):
    nEvt = citDict['nEvt']
    
    
    with open(f"table-{fileName}.dat","w") as dataFileOut:
        c = f"{'CIT0'.center(448)} {'CIT1'.center(448)} "
        g = f"{'HG'.center(223)} {'LG'.center(223)} "*2
        ch = ' '.join([f'CH{i:02d}'.ljust(6,' ')
                       for i in range(32)])
        dataFileOut.write(f"{c}\n{g}\n{ch} {ch} {ch} {ch} \n")
        
        for i in range(nEvt):
            dataFileOut.write(fileChWrite(adcVals[:,i]))

        mvals = np.mean(adcVals, axis=1)
        stdvals = np.std(adcVals, axis=1)

        dataFileOut.write("\nMEAN VALUES:\n")
        dataFileOut.write(csl.fileChWrite(mvals))

        dataFileOut.write("\nSTD DEVs:\n")
        dataFileOut.write(csl.fileChWrite(stdvals))

def citDictToArray(citDict):
    nCit=2
    gains=2
    channels=32
    c0lgOff = 32
    c1hgOff = 64
    c1lgOff = 96

    adcArray = np.zeros((nCit*gains*channels,citDict['nEvt']))

    for i in range(channels):
        adcArray[i,:]         = citDict['cit0'][f"ch{i:02d}"]['hg']
        adcArray[i+c0lgOff,:] = citDict['cit0'][f"ch{i:02d}"]['lg']
        adcArray[i+c1hgOff,:] = citDict['cit1'][f"ch{i:02d}"]['hg']
        adcArray[i+c1lgOff,:] = citDict['cit1'][f"ch{i:02d}"]['lg']

    return adcArray

def argToList(args,compList):
    if type(args) == str:
        if args == "all":
            args = compList
        elif args in compList:
            args = [args]
        else:
            raise ValueError(f"Selezione non valida: {args}")
    elif set(args).issubset(compList) is False:
        raise ValueError(f"Selezione non valida: {args}")

    return args

def getProbeRegVal(cit,gain,ch,probe):
    pName = probe.upper()
    cN = cit.lower()
    gN = gain.lower()
    chN = ch.lower()

    if chN not in chToNum.keys():
        raise ValueError(f"{ch} non valido!")
    
    if cN not in citToReg.keys():
        raise ValueError(f"{cN} non valido!")
    
    if gN not in hglgToVal.keys():
        raise ValueError(f"{gN} non valido!")

    if pName not in probeNameToReg.keys():
        raise ValueError(f"{pName} non valido!")

    cN = f"CIT{citToReg[cN]}"
    chN = int(chToNum[chN])
    gN = gN.upper()

    if pName != "OUTPA":
        probeReg = probeNameToReg[pName].format(cN,gN)
        probeVal = f"{1<<(31-chN):08x}"
    else:
        hglgStr = '10' if gN == "HG" else '01'
        if chN <= 15:
            nBefore = chN*'00'
            nAfter = (15-chN)*'00'
            gRegStr = "HG"
        else:
            nBefore = (chN-16)*'00'
            nAfter = (31-chN)*'00'
            gRegStr = "LG"

        pValBin = int(f"{nBefore}{hglgStr}{nAfter}",2)

        probeReg = probeNameToReg[pName].format(cN,gRegStr)
        probeVal = f"{pValBin:08x}"

    if probeReg not in regs.keys():
        raise ValueError(f"{probeReg} non valido!")

    return probeReg,probeVal
        
def getMeansOverPdst(dataValues,pdstDict,nevtMeans=None):
    meanDict = {'cit0':{f'ch{chn:02d}':{'hg':{'mean':0,
                                              'stddev':0},
                                        'lg':{'mean':0,
                                              'stddev':0}}
                        for chn in range(32)},
                'cit1':{f'ch{chn:02d}':{'hg':{'mean':0,
                                              'stddev':0},
                                        'lg':{'mean':0,
                                              'stddev':0}}
                        for chn in range(32)}}

    for cit in ['cit0','cit1']:
        for ch in [f'ch{d:02d}' for d in range(32)]:
            for g in ['hg','lg']:
                pdstVal = pdstDict[cit][ch][g]['mean']
                pdstStd = pdstDict[cit][ch][g]['stddev']
                pdstThr = pdstVal+3*pdstStd
                
                valsOverPdst = [dd for dd in dataValues[cit][ch][g] 
                                if dd > pdstThr]

                meanDict[cit][ch][g]['mean'] = np.mean(valsOverPdst)
                meanDict[cit][ch][g]['stddev'] = np.std(valsOverPdst)

    if nevtMeans is not None:
        meanDict.update({'nEvt':nevtMeans})

    return meanDict

# -*- coding: utf-8 -*-
"""
- sistemare la parte di impulsatore
- migliorare il riconoscimento dei pattern usando group
- migliorare prompt usando regex
- convertire ad oggetti
"""


import os
import copy
import serial
import serial.tools.list_ports
import re
from collections import defaultdict
from datetime import date
import time
import threading as th

fileConfName = "seriale.conf"
fileNameHead = "fromSerial"

dateT = str(date.today())
hours = "{:02d}".format(int(time.localtime(time.time())[3]))
mins = "{:02d}".format(int(time.localtime(time.time())[4]))
secs = "{:02d}".format(int(time.localtime(time.time())[5]))

timeDataStr = dateT+"-"+hours+mins+secs
fileOutputName = fileNameHead+"-"+timeDataStr+".dat"

elapsedTime = [False]

startWord = b'FE'
stopWord = b'GH'

numBytesAfterStartWord = 232

unitList = ['pv','nv','uv','mv','v','kv','ps','ns','us','ms','s','g','b','d']
unitConv = { # converte in mV o in ns
        'v' : {'p' : 1e-9,
               'n' : 1e-6,
               'u' : 1e-3,
               'm' : 1,
               'v' : 1e+3,
               'k' : 1e+6
               },
        's' : {
                'p' : 1e-3,
                'n' : 1,
                'u' : 1e+3,
                'm' : 1e+6,
                's' : 1e+9
                },
        'g' : {
                'l' : 'l',
                'h' : 'h',
                'g' : 'lh',
                'c' : 'c', # guadagno per ingresso di calibrazione LG
                't' : 't' # guadagno per ingresso di calibrazione HG
                },
        'b' : {
                'b' : 1
                },
        'd' : {
                'd' : 1
                },
        'a' : {
                'a' : 1
                },
        'p' : {
                'p' : 1
                },
        }
        
defaultParam = {
        'v'  : 'mv',
        's'  : 'ns',
        'g'  : 'g',
        'b'  : 'b',
        'd'  : 'd',
        'a'  : 'a',
        'p' : 'p'
        }

numericPattern = "([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)*)"
unitPattern = "([pnumk]?V|[pnumk]?s|[hlct]?g|b|d|a|p)"
errorPattern = "(\({numP}+{unitP}?\))".format(numP = numericPattern, unitP = unitPattern)
paramPattern = "(?i)^{numP}+{unitP}?{errP}?(,{numP}+{unitP}?{errP}?)*$".format(numP = numericPattern, unitP = unitPattern, errP = errorPattern)

feedbackCaps = [fCap for fCap in range(1575,0,-25)]

gainBitsToHGGain = {f"{bits:06b}" : round(15000/cap,3) for bits,cap in enumerate(feedbackCaps)}
gainBitsToLGGain = {f"{bits:06b}" : round(1500/cap,3) for bits,cap in enumerate(feedbackCaps)}
gainBitsToInCALIBGain = {f"{bits:06b}" : round(3000/cap,3) for bits,cap in enumerate(feedbackCaps)}

HGGainToGainBits = {v : k for k,v in gainBitsToHGGain.items()}
LGGainToGainBits = {v : k for k,v in gainBitsToLGGain.items()}
InCALIBGainToGainBits ={v : k for k,v in gainBitsToInCALIBGain.items()}

HGValidGains = list(HGGainToGainBits.keys())
LGValidGains = list(LGGainToGainBits.keys())
InCALIBValidGains = list(InCALIBGainToGainBits.keys())

def HGtoLGGain(hggain):
    return gainBitsToLGGain[HGGainToGainBits[hggain]]

def nearestTo(val,valList):
    centersList = []
    
    if val < valList[0]:
        return valList[0]
    elif val > valList[-1]:
        return valList[-1]
    else:
        valListLen = len(valList)
        
        for i in range(1,valListLen):
            centersList.append(valList[i-1]+(valList[i]-valList[i-1])/2)
    
        for i,v in enumerate(valList):
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
              f"al valore più vicino: {nearestGain}") #viene già fatto in paramsPrompt, si potrebbe anche togliere
    
    return gainBits

def setGainParam(fileNames,paramList,CtestHG = False, CtestLG = False,
                 PAdisable = False):
    gainVals = []

    hgEmpty = None in paramList['hg']
    lgEmpty = None in paramList['lg']
    
    if not hgEmpty and not lgEmpty:
        for i,f in enumerate(fileNames):
            inLGGain = paramList['lg'][i][0][0]
            inHGGain = paramList['hg'][i][0][0]
            
            if (CtestHG or CtestLG) is False:
                lgGainBits = getGainBits(inLGGain,LGGainToGainBits,
                                         LGValidGains)
                hgGainBits = getGainBits(inHGGain,HGGainToGainBits,
                                         HGValidGains)
            else:
                lgGainBits = getGainBits(inLGGain,InCALIBGainToGainBits,
                                         InCALIBValidGains)
                hgGainBits = getGainBits(inHGGain,InCALIBGainToGainBits,
                                         InCALIBValidGains)

            lastBits = f"{int(CtestHG)}{int(CtestLG)}{int(PAdisable)}"

            registerGain = f"{hgGainBits}{lgGainBits}{lastBits}"
            
            gainVals.append(f"{registerGain}")

    return gainVals

def setGain(valGain, gainLine="all",
            CtestHG = False, CtestLG = False, PAdisable = False):
    
    gainL = gainLine.lower()
    
    if gainL == "hg":
        if (CtestHG or CtestLG) is False:
            lgGainBits = getGainBits(0,LGGainToGainBits,
                                     LGValidGains)
            hgGainBits = getGainBits(valGain,HGGainToGainBits,
                                     HGValidGains)
        else:
            lgGainBits = getGainBits(0,InCALIBGainToGainBits,
                                     InCALIBValidGains)
            hgGainBits = getGainBits(valGain,InCALIBGainToGainBits,
                                     InCALIBValidGains)

        lastBits = f"{int(CtestHG)}{int(CtestLG)}{int(PAdisable)}"

        registerGain = f"{hgGainBits}{lgGainBits}{lastBits}"

    elif gainL == "lg":
        if (CtestHG or CtestLG) is False:
            lgGainBits = getGainBits(valGain,LGGainToGainBits,
                                     LGValidGains)
            hgGainBits = getGainBits(0,HGGainToGainBits,
                                     HGValidGains)
        else:
            lgGainBits = getGainBits(valGain,InCALIBGainToGainBits,
                                     InCALIBValidGains)
            hgGainBits = getGainBits(0,InCALIBGainToGainBits,
                                     InCALIBValidGains)

        lastBits = f"{int(CtestHG)}{int(CtestLG)}{int(PAdisable)}"

        registerGain = f"{hgGainBits}{lgGainBits}{lastBits}"

    else:

        if type(valGain) is not dict:
            raise ("Errore! E' necessario utilizzare un dizionario"
                    " per impostare entrambe le linee di guadagno.\n"
                    "Usare setGain({\"hg\":xxx,\"lg\":yyy})")
        else:
            if (CtestHG or CtestLG) is False:
                lgGainBits = getGainBits(valGain["lg"],LGGainToGainBits,
                                         LGValidGains)
                hgGainBits = getGainBits(valGain["hg"],HGGainToGainBits,
                                         HGValidGains)
            else:
                lgGainBits = getGainBits(valGain["lg"],InCALIBGainToGainBits,
                                         InCALIBValidGains)
                hgGainBits = getGainBits(valGain["hg"],InCALIBGainToGainBits,
                                         InCALIBValidGains)
    
            lastBits = f"{int(CtestHG)}{int(CtestLG)}{int(PAdisable)}"
    
            registerGain = f"{hgGainBits}{lgGainBits}{lastBits}"
    
    return registerGain

def setImpParam(fileNames,paramList,outInverted = False):
    voltStr = []
    pulseStr = []
    
    mvEmpty = None in paramList['mv']
    nsEmpty = None in paramList['ns']
    
    if not mvEmpty and not nsEmpty:
        for i,f in enumerate(fileNames):
            mvVal = float(paramList['mv'][i][0])/1000
            nsVal = float(paramList['ns'][i][0])/1e+9
            
            highVal = 0
            lowVal = 0
            
            if outInverted is False:
                if mvVal > 0:
                    highVal = mvVal
                    lowVal = 0
                    highSign = "+"
                    lowSign = ""
                else:
                    highVal = 0
                    lowVal = -mvVal
                    highSign = ""
                    lowSign = "-"
            else:
                if mvVal > 0:
                    highVal = 0
                    lowVal = mvVal
                    highSign = ""
                    lowSign = "-"
                else:
                    highVal = -mvVal
                    lowVal = 0
                    highSign = "+"
                    lowSign = ""
                    
            voltStr.append("VOLT:LOW {lowS}{lowV}; HIGH {highS}{highV}\n".format(lowS = lowSign, lowV = lowVal, highS = highSign, highV = highVal))

            if nsVal < 0: # non è possibile avere durata dell'impulso negativa
                nsVal *= -1

            pulseStr.append("PULSE:WIDTH {}\n".format(nsVal))

    else:
        raise Exception("Errore! Inserire almeno un valore per ampiezza e durata dell'impulso!")
            
    return voltStr,pulseStr

def impOutOff(serImp):
    serImp.write(b'OUTPUT:STATE OFF\n')

def impOutOn(serImp):
    serImp.write(b'OUTPUT:STATE ON\n')


def sendImpPulse(serImp,cmdStr,freq,outInverted = False):
    freqStr = "FREQUENCY {}\n".format(freq)
    
    if outInverted is True:
        invertStr = b'OUTP:POL INV\n'
    else:
        invertStr = b'OUTP:POL NORM\n'
    
    print(f"Imposto parametri:\n___________\n"
          f"{freqStr}{cmdStr}{invertStr.decode()}___________")
    
    impOutOff(serImp)
    serImp.write(freqStr.encode())
    serImp.write(cmdStr.encode())
    serImp.write(invertStr)
    serImp.write(b'FUNC PULSE\n')
    impOutOn(serImp)

def sendImpBurst(serImp,pulsNum,cmdStr,freq,pulsW,pulsD,
                 risingTime=5e-9,fallingTime=5e-9,outInverted = False):

    burstPeriod = 1/float(freq)

    period = pulsW+pulsD+risingTime+fallingTime
    
    burstPeriodStr = f"BURST:INTERNAL:PERIOD {burstPeriod}\n"
    
    periodStr = f"PULSE:PERIOD {period}\n"
    
    if outInverted is True:
        invertStr = b'OUTP:POL INV\n'
    else:
        invertStr = b'OUTP:POL NORM\n'
    
    print(f"Imposto parametri:\n___________\n"
          f"{burstPeriodStr}{periodStr}"
          f"{cmdStr}{invertStr.decode()}___________")
    
    impOutOff(serImp)
    serImp.write(periodStr.encode())
    serImp.write(cmdStr.encode())
    serImp.write(invertStr)
    serImp.write(b'FUNC PULSE\n')
    serImp.write(b'BURST:MODE TRIGGERED\n')
    serImp.write(burstPeriodStr.encode())
    serImp.write(f"BURST:NCYCLES {pulsNum}\n".encode())
    serImp.write(b'TRIGGER:SOURCE IMMEDIATE\n')
    serImp.write(b'BURST:STATE ON\n')
    impOutOn(serImp)

def burstImpOff(serImp):
    serImp.write(b'BURST:STATE OFF\n')

def stopRead(p):
    p[0] = True

def connectToSerial(comConf):
    try:
        print("Connessione alla porta "+comConf['comPort']+" baudrate "+comConf['baudRate']+"...")
        ser = serial.Serial(port = comConf['comPort'], baudrate = int(comConf['baudRate']), timeout = 0, parity = serial.PARITY_NONE)
    except serial.SerialException as e:
        print("Impossibile connettersi alla porta! Errore: {}".format(e))
    return ser

def disconnectFromSerial(ser):
    print("Uscita...")
    ser.close()

def dummyRead(ser):
    print("Eliminazione dati residui nella fifo...")
    while ser.in_waiting > 0:
        ser.read(ser.in_waiting)

def saveDataFromSerial(ser,comConf,fileName,paramString,confParameters):
    serData = b''
    try:
        print("Inizio acquisizione... Premere CNTRL-C per uscire...\n")
        fileOutput = open(fileName+fileOutputName,"wb")
        
        fileOutput.write(f"{paramString}\n".encode('utf-8'))
        for k,v in confParameters.items():
            fileOutput.write(f"{k}={v}\n".encode('utf-8'))
        
        t = th.Timer(int(comConf['acqTime']), stopRead, [elapsedTime])
        t.start()
        t1 = time.perf_counter()
        print("Timer partito...")
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        while elapsedTime[0] is False:
            if ser.in_waiting > 0:
                serData = ser.read(ser.in_waiting)
                fileOutput.write(serData)
        t2 = time.perf_counter()
        print(f"Acquisizione finita, sono passati {t2-t1:.3f} secondi")
        
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        t.cancel()
        elapsedTime[0] = False
        fileOutput.close()
        writeLog(fileName+fileOutputName,paramString)

    except KeyboardInterrupt:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        t.cancel()
        fileOutput.close()
        writeLog(fileName+fileOutputName,paramString)
        raise Exception("Chiusura programma...")

def genStringsForFile(s,m,n,hg,lg,impDist=None,
                      holdDelay=None,shaperTConst=None,phase=None):
    fStr = f"{s}_"
    lStr = ""
    mErrPres = False
    nErrPres = False
    hgErrPres = False
    lgErrPres = False
    
    mPres = (m != None)
    nPres = (n != None)
    hgPres = (hg != None)
    lgPres = (lg != None)
    bPres = (impDist != None)
    holdPres = (holdDelay != None)
    shapPres = (shaperTConst != None)
    phasePres = (phase != None)

    if mPres:
        mErrPres = (len(m) == 2)
        fStr += f"{m[0]:.0f}mv-"
        lStr += f"V={m[0]:.3f}mv "
    if mErrPres:
        fStr += f"({m[-1]:.0f}mv)-"
        lStr += f"Verr={m[-1]:.3f}mv "
    if nPres:
        nErrPres = (len(n) == 2)
        fStr += f"{n[0]:.3f}ns-"
        lStr += f"T={n[0]:.3f}ns "
    if nErrPres:
        fStr += f"({n[-1]:.3f}ns)-"
        lStr += f"Terr={n[-1]:.3f}ns "
    if hgPres:
        hgErrPres = (len(hg) == 2)
        fStr += f"{hg[0][0]:.3f}hg-"
        lStr += f"HG={hg[0][0]:.3f}g "
    if hgErrPres:
        fStr += f"({hg[-1][0]:.3f}hg)-"
        lStr += f"HGerr={hg[-1][0]:.3f}g "
    if lgPres:
        lgErrPres = (len(lg) == 2)
        fStr += f"{lg[0][0]:.3f}lg-"
        lStr += f"LG={lg[0][0]:.3f}g "
    if lgErrPres:
        fStr += f"({lg[-1][0]:.3f}lg)-"
        lStr += f"LGerr={lg[-1][0]:.3f}g "

    if bPres:
        fStr += f"D{impDist[-1]:.0f}ns-"
        lStr += f"impDist={impDist[-1]:.3f}ns "

    if holdPres:
        fStr += f"hold{int(holdDelay[-1]):d}-"
        lStr += f"holdDelay={int(holdDelay[-1])*10:d}ns "
    
    if shapPres:
        fStr += f"ssh{int(shaperTConst[0]):d}-"
        lStr += f"sshTconst={int(shaperTConst[0]):d} "

    if phasePres:
        fStr += f"ph{int(phase[0]):d}ns-"
        lStr += f"phase={int(phase[0]):d}ns"

    return fStr,lStr

def genFileNameList(suffixName,mvpar,nspar,gpar,impDistpar,
                    holdDelaypar,shapTpar,phasepar):
    fileNames = []
    paramStringList = []
    hgpar = []
    lgpar = []
    paramList = defaultdict(list)

    if len(mvpar) == 0:
        mvpar.append(None)
    if len(nspar) == 0:
        nspar.append(None)
    if len(gpar) == 0:
        gpar.append(None)
    if len(impDistpar) == 0:
        impDistpar.append(None)
    if len(holdDelaypar) == 0:
        holdDelaypar.append(None)
    if len(shapTpar) == 0:
        shapTpar.append(None)
    if len(phasepar) == 0:
        phasepar.append(None)

    coupledGains = False
    for gPar in gpar:
        if gPar is None:
            hgpar.append(None)
            lgpar.append(None)
        elif gPar[0][-1] == 'h':
            hgpar.append(gPar)
        elif gPar[0][-1] == 'l':
            lgpar.append(gPar)
        elif gPar[0][-1] == 'lh':
            coupledGains = True
            hgpar.append(gPar)
            lgEquivalentPar = copy.deepcopy(gPar)
            lgEquivalentPar[0][0] = HGtoLGGain(gPar[0][0])
            lgpar.append(lgEquivalentPar)
        elif gPar[0][-1] == 'c':
            lgpar.append(gPar)
        elif gPar[0][-1] == 't':
            hgpar.append(gPar)

    if coupledGains is False:
        for hgPar in hgpar:
            for lgPar in lgpar:
                for nsPar in nspar:
                    for mvPar in mvpar:
                        for bPar in impDistpar:
                            for holdPar in holdDelaypar:
                                for shapTPar in shapTpar:
                                    for phasePar in phasepar:
                                    
                                        fileName, listName = genStringsForFile(suffixName,mvPar,nsPar,
                                                                               hgPar,lgPar,bPar,holdPar,
                                                                               shapTPar,phasePar)
                                        
                                        fileNames.append(fileName)
                                        paramStringList.append(listName)
                                        paramList['mv'].append(mvPar)
                                        paramList['ns'].append(nsPar)
                                        paramList['hg'].append(hgPar)
                                        paramList['lg'].append(lgPar)
                                        paramList['b'].append(bPar)
                                        paramList['d'].append(holdPar)
                                        paramList['a'].append(shapTPar)
                                        paramList['p'].append(phasePar)
    else:
        for l,hgPar in enumerate(hgpar):
            for nsPar in nspar:
                for mvPar in mvpar:
                    for bPar in impDistpar:
                        for holdPar in holdDelaypar:
                            for shapTPar in shapTpar:
                                for phasePar in phasepar:
                                
                                    fileName, listName = genStringsForFile(suffixName,mvPar,nsPar,
                                                                           hgPar,lgpar[l],bPar,holdPar,
                                                                           shapTPar,phasePar)
                                    
                                    fileNames.append(fileName)
                                    paramStringList.append(listName)
                                    paramList['mv'].append(mvPar)
                                    paramList['ns'].append(nsPar)
                                    paramList['hg'].append(hgPar)
                                    paramList['lg'].append(lgpar[l])
                                    paramList['b'].append(bPar)
                                    paramList['d'].append(holdPar)
                                    paramList['a'].append(shapTPar)
                                    paramList['p'].append(phasePar)

    return fileNames,paramStringList,paramList

def prompt(text, *opts, default=""):  
    retVal = ""
    defStr = ""
    inputOK = False

    if default != "":
        defStr = f" default='{default}' "

    text += "("
    for i,opt in enumerate(opts):
        separator = "|"

        if i == len(opts)-1:
            separator = f"){defStr}: "

        text += opt + separator
    
    while inputOK is False:
        retVal = input(text)
        if retVal in opts:
            inputOK = True
        elif retVal == "" and default != "":
            if default in opts:
                retVal = default
                inputOK = True
            else:
                inputOK = False
        else:
            inputOK = False
            
    return retVal

def paramsPrompt(strPrompt):
    parOK = False
    
    while parOK is False:
        parIn = input(strPrompt)
        
        parNoSpaces = parIn.replace(' ','') #inutile! cambiare regex piuttosto
        paramsMatch = re.match(paramPattern,parNoSpaces)
    
        if paramsMatch is not None:
            paramsFromInput = paramsMatch.group().split(',') #split inutile, cambiare regex
            parOK = True
    
    params = []
    
    for pi in paramsFromInput: #ancora inutile, si può scrivere regex in modo da usare direttamente paramsFromInput
        params.append(pi)
    
    paramsDict = defaultdict(list)
    
    for p in params:
        p = p.lower()
        
        valAndErrs = p.split('(') #inutile, cambia regex anche per le righe successive
        
        pval = valAndErrs[0]
        
        errPresent = (len(valAndErrs) == 2)

        if re.search("^{numP}$".format(numP = numericPattern),pval) is not None: # se è stato inserito solo il valore numerico senza unità di misura aggiunge 'mv'
            pval+='mv'

        if errPresent:
            perrMatch = re.match("{numP}".format(numP = numericPattern),valAndErrs[1])
            if perrMatch is not None:
                perr = perrMatch.group()

        unitMatch = re.search("(?i)"+unitPattern,pval)
        
        if unitMatch is not None:
            unit = unitMatch.group()
            keyParam = defaultParam[unit[-1]]
            numericIn = float(pval[:pval.find(unit)])
            if unit[0] not in unitConv['g']:
                valToAppend = numericIn*unitConv[unit[-1]][unit[0]]
            else:
                if unit[0] == 'h' or unit[0] == 'g':
                    if numericIn not in HGValidGains:
                        gainVal = nearestTo(numericIn,HGValidGains)
                        print(f"{numericIn} non impostabile, imposto il"
                              f" guadagno al valore più vicino: {gainVal}")
                    else:
                        gainVal = numericIn
                elif unit[0] == 'l':
                    if numericIn not in LGValidGains:
                        gainVal = nearestTo(numericIn,LGValidGains)
                        print(f"{numericIn} non impostabile, imposto il"
                              f" guadagno al valore più vicino: {gainVal}")
                    else:
                        gainVal = numericIn
                elif unit[0] == 'c' or unit[0] == 't':
                    if numericIn not in InCALIBValidGains:
                        gainVal = nearestTo(numericIn,InCALIBValidGains)
                        print(f"{numericIn} non impostabile, imposto il"
                              f" guadagno al valore più vicino: {gainVal}")
                    else:
                        gainVal = numericIn
 
                valToAppend = [gainVal,unitConv[unit[-1]][unit[0]]]

            if valToAppend not in paramsDict[keyParam]:
                if errPresent:
                    if unit[0] not in unitConv['g']:
                        errToAppend = float(perr)*unitConv[unit[-1]][unit[0]]
                    else:
                        errToAppend = [float(perr),unitConv[unit[-1]][unit[0]]]
                    paramsDict[keyParam].append([valToAppend,errToAppend])
                elif not errPresent:
                    paramsDict[keyParam].append([valToAppend])
                else:
                    raise Exception("Errore nel parsing dell'input!")

            paramsDict[keyParam].sort()
            
        else:
            raise Exception("Errore nel parsing dell'input!")

    return paramsDict
    

def loadConf():
    conf = {}
    with open(fileConfName,"r") as fileConf:
        for line in fileConf:
            print(line)
            lineLenght = len(line)
            sep = line.find("=")
            
            if sep > -1:
                conf[line[:sep]] = line[sep+1:lineLenght-1]
                
            else:
                return -1
            
    return conf

def searchConf():
    return os.path.isfile(fileConfName)

def serialPrompt(portPromptStr,baudPromptStr,comList,comMaxNum):
    comPort = ""
    baudRate = ""

    if comMaxNum>0:
        print(portPromptStr)
    
        for i,com in enumerate(comList):
            print(str(i)+") "+com.description+"\n")
    
        while (comPort.isnumeric() is False) or (int(comPort) > comMaxNum): 
            comPort = input("(Inserire un valore numerico compreso fra 0 e "+str(comMaxNum)+"): ")
            
        comPort = comList[int(comPort)].device
            
    else:
        raise Exception("Non sono state trovate porte!")
                
    while baudRate.isnumeric() is False:
        baudRate = input(baudPromptStr)
            
    return comPort,baudRate
    
def newConf():
    comList = serial.tools.list_ports.comports()
    comMaxNum = len(comList) - 1
    saveConf = ""
    confOK = False

    conf = {
            "comPort" : "",
            "baudRate" : "",
            "acqTime" : 0,
            "impComPort" : "",
            "impBaudRate" : ""
            }

    if comMaxNum == 0:
        raise Exception("E' presente solo una porta seriale, impossibile colegare scheda ed impulsatore!")

    # seleziona connessione seriale per la scheda

    while confOK is False:

        acqTime = ""
        
        comPort,baudRate = serialPrompt("Scegliere la porta della scheda: ","Inserire baudrate della scheda: ",comList,comMaxNum)
        
        conf['comPort'] = comPort        
        conf['baudRate'] = baudRate

        impComPort,impBaudRate = serialPrompt("Scegliere la porta dell'impulsatore: ","Inserire baudrate dell'impulsatore: ",comList,comMaxNum)
        
        conf['impComPort'] = impComPort        
        conf['impBaudRate'] = impBaudRate

        while acqTime.isnumeric() is False:
            acqTime = input("Inserire la durata delle acquisizioni: ")
        
        conf['acqTime'] = acqTime
        
        saveConf = prompt("Salvare la configurazione? ","s","n", default = "n")
        
        if saveConf == "s":
            with open(fileConfName,"w") as fileConf:
                fileConf.write("comPort="+comPort+"\n")
                fileConf.write("baudRate="+baudRate+"\n")
                fileConf.write("acqTime="+acqTime+"\n")
                fileConf.write("impComPort="+impComPort+"\n")
                fileConf.write("impBaudRate="+impBaudRate+"\n")
                confOK = True
                
        else:
            confOK = False
            
    return conf

def writeLog(fileName,paramString):
    
    numEvt = 0
    
    startPos = []
    stopPos = []
    
    fnhStr = fileNameHead+"-"
    
    date = fileName[fileName.find(fnhStr):-len(".dat")]
    
    logFileName = fileName[:-len(".dat")]+".log"
    
    lenStartWord = len(startWord)
    lenStopWord = len(stopWord)
    
    with open(fileName,"rb") as serFile:
        serFileData = serFile.read()
    
    if len(serFileData) != 0:
        
        firstStartIndex = serFileData.find(startWord)
        
        lastStopIndex = 0
        for i in range(0,len(serFileData)):
            if serFileData[i:i+lenStopWord] == stopWord:
                lastStopIndex = i
           
        for i in range(firstStartIndex,lastStopIndex+lenStopWord):
            startIndex = i+lenStartWord
            endIndex = i+lenStartWord+numBytesAfterStartWord
        
            if (serFileData[i:startIndex] == startWord) and (serFileData[endIndex:endIndex+lenStopWord] == stopWord):
                startPos.append(i)
                stopPos.append(endIndex)
    
        numEvt=len(startPos)

    else:
        print("Nessun dato dalla seriale!")

    with open(logFileName,"w") as logFile:
        logFile.write(f"--- {date} ---\n")
        logFile.write(f"PARAMETERS {paramString}\n")
        logFile.write(f"startWord={startWord} stopWord={stopWord}\n")
        logFile.write(f"numEvt={str(numEvt)}\n")
        for i in range(0,numEvt):
            logFile.write(f"evt{str(i)} startPos={str(startPos[i])} stopPos={str(stopPos[i])}\n")

# -*- coding: utf-8 -*-

"""
- migliorare i prompt usando regex
- usare multiprocessing per plottare i grafici
- convertire ad oggetti
"""

import os
import re
import numpy as np
import matplotlib.pyplot as plt
from io import StringIO
from serialeLib import fileNameHead
import matplotlib.cm as cm
from scipy.optimize import curve_fit

EXIT_FROM_PROMPT = "EXIT_FROM_PROMPT"

resultsDirName = "results"
dataFileName = "data"
hexDataFileName = "HEXdata"
meansFileName = "means"

resDirHead = resultsDirName + "-"
dataFileHead = dataFileName + "-"
hexDataFileHead = hexDataFileName + "-"
meansFileHead = meansFileName + "-"


fNameHead = "-" + fileNameHead

rangePattern = "\[[\d]+-[\d]+\]"

PMT = {
       "CIT0" : {
                   "CH0" : "$P0_{1009}$",
                   "CH1" : "$P0_{1013}$",
                   "CH2" : "PMT2",
                   "CH3" : "PMT1",
                   "CH4" : "N.C.",
                   "CH5" : "$BDC7086$",
                   "CH6" : "N.C.",
                   "CH7" : "$BDB6990$",
                   "CH8" : "N.C."
                   },
        "CIT1" : {
                   "CH0" : "N.C.",
                   "CH1" : "N.C.",
                   "CH2" : "PMT2",
                   "CH3" : "PMT2",
                   "CH4" : "N.C.",
                   "CH5" : "$BDC7086$",
                   "CH6" : "N.C.",
                   "CH7" : "$BDB6990$",
                   "CH8" : "N.C."
                }
       }

PMTraw = {
        "CIT0" : {
                   "CH0" : "P01009",
                   "CH1" : "P01013",
                   "CH2" : "PMT2",
                   "CH3" : "PMT1",
                   "CH4" : "nc",
                   "CH5" : "BDC7086",
                   "CH6" : "nc",
                   "CH7" : "BDB6990",
                   "CH8" : "nc",
                   },
        "CIT1" : {
                   "CH0" : "nc",
                   "CH1" : "nc",
                   "CH2" : "PMT2",
                   "CH3" : "PMT1",
                   "CH4" : "nc",
                   "CH5" : "BDC7086",
                   "CH6" : "nc",
                   "CH7" : "BDB6990",
                   "CH8" : "nc",
                   }
       }

PMTGain = {
        900 : {
                "BDC7086" : {
                            "anodo" : 1.55e6,
#                            "dinodo" : 1.15e6
                            "dinodo" : 1.15e6
                            },
                "BDB6990" : {
                            "anodo" : 5.71e6,
#                            "dinodo" : 4.53e6
                            "dinodo" : 4.54e6
                            }
                }
        }

adcToPCDict = {
        "CIT0" : {"HG" : {
                          "05" : {600.0 : {"adcPerPC" : 52.15, "interc" : 122},
                                   30.0  : {"adcPerPC" : 9.3, "interc" : 118},
                                   9.524 : {"adcPerPC" : 3.05, "interc" : 124.7}},
                          "07" : {600.0 : {"adcPerPC" : 52.15, "interc" : 122},
                                   30.0  : {"adcPerPC" : 9.3, "interc" : 118},
                                   9.524 : {"adcPerPC" : 3.05, "interc" : 124.7}},
                          "00" : {600.0 : {"adcPerPC" : 52.15, "interc" : 122},
                                   30.0  : {"adcPerPC" : 9.3, "interc" : 118},
                                   9.524 : {"adcPerPC" : 3.05, "interc" : 124.7}},
                          "01" : {600.0 : {"adcPerPC" : 52.15, "interc" : 122},
                                   30.0  : {"adcPerPC" : 9.3, "interc" : 118},
                                   9.524 : {"adcPerPC" : 3.05, "interc" : 124.7}},
                          "02" : {600.0 : {"adcPerPC" : 52.15, "interc" : 122},
                                   30.0  : {"adcPerPC" : 9.3, "interc" : 118},
                                   9.524 : {"adcPerPC" : 3.05, "interc" : 124.7}},
                          "03" : {600.0 : {"adcPerPC" : 52.15, "interc" : 122},
                                   30.0  : {"adcPerPC" : 9.3, "interc" : 118},
                                   9.524 : {"adcPerPC" : 3.05, "interc" : 124.7}}
                          },
                  "LG" : {"05" : {600.0 : {"adcPerPC" : 1, "interc" : 0},
                                   30.0  : {"adcPerPC" : 1, "interc" : 0},
                                   9.524 : {"adcPerPC" : 1, "interc" : 0}},
                          "07" : {600.0 : {"adcPerPC" : 1, "interc" : 0},
                                   30.0  : {"adcPerPC" : 1, "interc" : 0},
                                   9.524 : {"adcPerPC" : 1, "interc" : 0}}
                          }
                },
                          
        "CIT1" : {"HG" : {
                          "05" : {600.0 : {"adcPerPC" : 25.19, "interc" : 112},
                                   30.0  : {"adcPerPC" : 4.36, "interc" : 116},
                                   9.524 : {"adcPerPC" : 1.47, "interc" : 117.6}},
                          "07" : {600.0 : {"adcPerPC" : 25.19, "interc" : 112},
                                   30.0  : {"adcPerPC" : 4.36, "interc" : 116},
                                   9.524 : {"adcPerPC" : 1.47, "interc" : 117.6}},
                          "00" : {600.0 : {"adcPerPC" : 25.19, "interc" : 112},
                                   30.0  : {"adcPerPC" : 4.36, "interc" : 116},
                                   9.524 : {"adcPerPC" : 1.47, "interc" : 117.6}},
                          "01" : {600.0 : {"adcPerPC" : 25.19, "interc" : 112},
                                   30.0  : {"adcPerPC" : 4.36, "interc" : 116},
                                   9.524 : {"adcPerPC" : 1.47, "interc" : 117.6}},
                          "02" : {600.0 : {"adcPerPC" : 25.19, "interc" : 112},
                                   30.0  : {"adcPerPC" : 4.36, "interc" : 116},
                                   9.524 : {"adcPerPC" : 1.47, "interc" : 117.6}},
                          "03" : {600.0 : {"adcPerPC" : 25.19, "interc" : 112},
                                   30.0  : {"adcPerPC" : 4.36, "interc" : 116},
                                   9.524 : {"adcPerPC" : 1.47, "interc" : 117.6}}
                          },
                  "LG" : {
                          "05" : {600.0 : {"adcPerPC" : 1, "interc" : 0},
                                   30.0  : {"adcPerPC" : 1, "interc" : 0},
                                   9.524 : {"adcPerPC" : 1, "interc" : 0}},
                          "07" : {600.0 : {"adcPerPC" : 1, "interc" : 0},
                                   30.0  : {"adcPerPC" : 1, "interc" : 0},
                                   9.524 : {"adcPerPC" : 1, "interc" : 0}}
                          }
                }
        }

CH = {   'CH0':0, 'CH1':1, 'CH2':2, 'CH3':3, 'CH4':4, 'CH5':5, 'CH6':6, 'CH7':7,
         'CH8':8, 'CH9':9, 'CH10':10, 'CH11':11, 'CH12':12, 'CH13':13, 'CH14':14, 'CH15':15,
         'CH16':16, 'CH17':17, 'CH18':18, 'CH19':19, 'CH20':20, 'CH21':21, 'CH22':22, 'CH23':23,
         'CH24':24, 'CH25':25, 'CH26':26, 'CH27':27, 'CH28':28, 'CH29':29, 'CH30':30, 'CH31':31  }

GAIN = {'HG':0, 'LG':1}

CIT = {'CIT0':0, 'CIT1':1}

IGAIN = {v: k for k, v in GAIN.items()}
ICH = {v: k for k, v in CH.items()}
ICIT = {v: k for k, v in CIT.items()}

dataBUF = StringIO()
hexDataBUF = StringIO()
meansBUF = StringIO()
meansTxtBUF = StringIO()

def showFiles(directory = "",ext="", onlyDir = False):
    if directory != "":
        os.chdir(directory)

    filesInDir = os.listdir()

    numFilesInDir = len(filesInDir)
    
    if ext == "":
        space = ""
    else:
        space = " "

    extStr = ext+space
    print(f"Files {extStr}nella directory: \n .\n ..")

    for i,f in enumerate(filesInDir):
        noExt = (onlyDir is False and ext == "")
        extNoDir = (onlyDir is False and (f.find(ext)>0 or os.path.isdir(f)))
        sDir = (onlyDir is True and os.path.isdir(f))

        if noExt or extNoDir or sDir:
            print(f"{i}) {f}")

    return filesInDir,numFilesInDir

def selectFilePrompt():
    fd = ""
    fdToReturn = []
    selOK = False

    while selOK is False:
        filesInDir,numFilesInDir = showFiles(fd,ext=".dat")

        fd = ""

        fileSel = input("Selezionare un file da analizzare "+\
                        "(* per uscire, [num-num],[num-num],...,[num-num]"+\
                        " per selezionare insiemi di file): ")

        if fileSel.isnumeric() is True:
            fileSelINT = int(fileSel)

            if fileSelINT < numFilesInDir:
                fd = filesInDir[fileSelINT]
            else:
                print("Scegliere un numero da 0 a "+str(numFilesInDir-1))
                continue

        else:
            if fileSel == "*":
                fd = EXIT_FROM_PROMPT
            else:
                fileSelMatch = re.match(f"^{rangePattern}(,{rangePattern})*$",
                                        fileSel)
                if fileSelMatch is not None:
                    filesArr = fileSelMatch.group().split(",")
                    
                    for f in filesArr:
                        firstIndex = int(f[f.find("[")+1:f.find("-")])
                        lastIndex = int(f[f.find("-")+1:-1])
                        
                        if lastIndex < firstIndex:
                            firstIndex, lastIndex = lastIndex, firstIndex

                        for i in range(firstIndex,lastIndex+1):
                            fileToAdd = filesInDir[i]
                            if fileToAdd.find(".dat") > 0 and fileToAdd not in fdToReturn:
                                fdToReturn.append(fileToAdd)

                else:
                    if fileSel in filesInDir:
                        fd = fileSel
                    else:
                        print("Errore! File {} inesistente!".format(fileSel))
                        continue

        selOK = not os.path.isdir(fd)
        
    if len(fdToReturn) == 0:
        fdToReturn.append(fd)

    return fdToReturn

def selectDirectoryPrompt():
    fd = ""
    fdToReturn = []
    selOK = False

    while selOK is False:
        filesInDir,numFilesInDir = showFiles(fd,onlyDir=True)

        fd = ""

        fileSel = input("Selezionare una directory da analizzare "+\
                        "(* per uscire, [num-num],[num-num],...,[num-num]"+\
                        " per selezionare insiemi di file): ")

        if fileSel.isnumeric() is True:
            fileSelINT = int(fileSel)

            if fileSelINT < numFilesInDir:
                fd = filesInDir[fileSelINT]
            else:
                print("Scegliere un numero da 0 a "+str(numFilesInDir-1))
                continue

        else:
            if fileSel == "*":
                fd = EXIT_FROM_PROMPT
            else:
                fileSelMatch = re.match("^{rngP}(,{rngP})*$".format(rngP = rangePattern),fileSel)
                if fileSelMatch is not None:
                    filesArr = fileSelMatch.group().split(",")
                    
                    for f in filesArr:
                        firstIndex = int(f[f.find("[")+1:f.find("-")])
                        lastIndex = int(f[f.find("-")+1:-1])
                        
                        if lastIndex < firstIndex:
                            firstIndex, lastIndex = lastIndex, firstIndex

                        for i in range(firstIndex,lastIndex+1):
                            fileToAdd = filesInDir[i]
                            if fileToAdd.find(".dat") > 0 and fileToAdd not in fdToReturn:
                                fdToReturn.append(fileToAdd)

                else:
                    if fileSel in filesInDir:
                        fd = fileSel
                    else:
                        print("Errore! File {} inesistente!".format(fileSel))
                        continue

        selOK = not os.path.isdir(fd)
        
    if len(fdToReturn) == 0:
        fdToReturn.append(fd)

    return fdToReturn

def spanCIT(functionToCall,**kwargs):
    for nCIT in range(0,2):
        for nGain in range(0,2):
            for nChannel in range(0,32):
                res = functionToCall(nCIT,nGain,nChannel,*tuple(value for _ , value in kwargs.items()))
    return res

def getDACSVal(fileSelected, numEvt, startWord, stopWord,\
               startPos, stopPos, getBinary=True):
    bytesOfDACSLine = 192
    bytesOfCountersLine = 40
    
    DACSVal = []
    countersVal = []
    DACSBinaryVal = []
    countersBinaryVal = []
    events = []
    
    startWordB = startWord.encode()

    with open(fileSelected,"rb") as serFile:
        serFileData = serFile.read()

    for i in range(0,numEvt):
        events.append(serFileData[startPos[i]+len(startWordB):stopPos[i]])
    
    for evt in events:
        DACSVal.append(evt[0:bytesOfDACSLine]) #debug
        countersVal.append(evt[bytesOfDACSLine:]) #debug       
        
        DACSInt = int.from_bytes(evt[0:bytesOfDACSLine], byteorder = 'big', signed = False) # converte il tipo da bytes a int
        cntInt = int.from_bytes(evt[bytesOfDACSLine:], byteorder = 'big', signed = False) # per poter usare binary_repr
        
        DACSInBinary = np.binary_repr(DACSInt,bytesOfDACSLine*8)
        cntInBinary = np.binary_repr(cntInt,bytesOfCountersLine*8)
        
        ### Parte di inversione per leggere correttamente i valori!
        DACSInBinaryInverted = []
        
        for i in range(0,len(DACSInBinary),4):
            DACSInBinaryInverted.append(DACSInBinary[i:i+4])
            
        DACSInBinaryInverted.reverse()
        
        DACSInBinaryInvertedString = ""
        
        for i in range(0,len(DACSInBinaryInverted),2):
            DACSInBinaryInvertedString += DACSInBinaryInverted[i+1] + DACSInBinaryInverted[i]

        DACSBinaryVal.append(DACSInBinaryInvertedString)
        countersBinaryVal.append(cntInBinary)
    
    if getBinary is True:
        return DACSBinaryVal,countersBinaryVal
    else:
        return DACSVal,countersVal

def makeCITArray(nCIT,nGain,nChannel, nEVT, Data, outCIT, outIntCIT):

    startIndex = (nChannel * 12) + (nGain * 384) + (nCIT * 768)
    stopIndex = startIndex + 12
    
    
    # aggiornamento 10/12/2020: dopo che Libero ha finito di generare il bitstream i due CITIROC saranno ordinati "correttamente" quindi bisognerà usare 1-nCit
    outCIT[1-nCIT][1-nGain][31-nChannel][nEVT] = Data[startIndex:stopIndex]
    outIntCIT[1-nCIT][1-nGain][31-nChannel][nEVT] = int(Data[startIndex:stopIndex],2)
    # outCIT[1-nCIT][1-nGain][31-nChannel][nEVT] = Data[startIndex:stopIndex]
    # outIntCIT[1-nCIT][1-nGain][31-nChannel][nEVT] = int(Data[startIndex:stopIndex],2)
    
    return 0

def getDataFromLog(fileSelected):
    numEFromLog = 0
    startWFromLog = ""
    stopWFromLog = ""
    paramStringFromLog = ""

    startPosFromLog = []
    stopPosFromLog = []

    if fileSelected != EXIT_FROM_PROMPT:
        fileNameLen = len(fileSelected)
        logFileName = fileSelected[0:fileNameLen-4]+".log"

        with open(logFileName,"r") as logFile:
            for line in logFile:
                startWordIndex = line.find("startWord")
                stopWordIndex = line.find("stopWord")
                numEvtIndex = line.find("numEvt")
                startPosIndex = line.find("startPos")
                stopPosIndex = line.find("stopPos")
                paramIndex = line.find("PARAMETERS ")
                
                if startWordIndex >= 0:
                    startWFromLog = line[len("startWord=b'"):stopWordIndex-2]
                if stopWordIndex >= 0:
                    stopWFromLog = line[stopWordIndex+len("stopWord=b'"):len(line)-3]
                if numEvtIndex >= 0:
                    numEFromLog = int(line[len("numEvt="):])
                if startPosIndex >= 0:
                    startPosFromLog.append(int(line[startPosIndex+len("startPos="):stopPosIndex]))
                    stopPosFromLog.append(int(line[stopPosIndex+len("stopPos="):len(line)-1]))
                
                if paramIndex >= 0:
                    paramStringFromLog = line[paramIndex+len("PARAMETERS "):-1]

        if startWFromLog == "" or stopWFromLog == "" or numEFromLog == "":
            raise Exception("File .log non corretto!")

        return numEFromLog,startWFromLog,stopWFromLog,startPosFromLog,stopPosFromLog,paramStringFromLog

def plotPrompt():
    cmd = input("Scegliere CITIROC, linea di guadagno e canale:\n\n"\
                "Sintassi: [cit<num>|all] [hg|lg|all] [ch<num>|ch<firstChannel>-ch<lastChannel>|all]"\
                "\nES. \"cit0 hg ch0\" oppure \"all hg ch2-ch31\"\n\n> ")

    cmdOK = re.match("(?i)(cit[0-1]|all)\s(hg|lg|all)\s(ch[0-3]?[0-9]|all)(-ch[0-3]?[0-9])?$",cmd)

    args = cmd.split(" ")

    nCIT = args[0].upper()
    nGAIN = args[1].upper()
    nCH = args[2].upper()

    if(nCIT == 'ALL'):
        citVal = ('CIT0','CIT1')
    elif nCIT in CIT:
        citVal = (nCIT,)
    else:
        citVal = (-1,)

    if(nGAIN == 'ALL'):
        gainVal = ('HG','LG')
    elif nGAIN in GAIN:
        gainVal = (nGAIN,)
    else:
        gainVal = (-1,)

    if(nCH == 'ALL'):
        chVal = []
        for i in range(0,32):
            chVal.append(ICH[i])
    else:
        if nCH.find("-") < 0:
            chVal = (nCH,)
        else:
            chVal = []
            extr = nCH.split("-")
            firstCHIndex = CH[extr[0]]
            lastCHIndex = CH[extr[1]]
            if(lastCHIndex > firstCHIndex):
                for i in range(firstCHIndex,lastCHIndex+1):
                    chVal.append(ICH[i])
            else:
                chVal = (-1,)

    if cmdOK is not None:
        return citVal,gainVal,chVal

    else:
        return (-1,),(-1,),(-1,)

def saveDataFile(nCIT,nGain,nChannel,fileSel,stDir,resDirName,intCIT):
    if not os.path.exists(resDirName):
        os.mkdir(resDirName)
    os.chdir(resDirName)

    firstIteration = (nCIT == 0 and nGain == 0 and nChannel == 0)
    lastIteration = (nCIT == 1 and nGain == 1 and nChannel == 31)

    if firstIteration:
        dataBUF.truncate(0)
        dataBUF.seek(0)
        hexDataBUF.truncate(0)
        hexDataBUF.seek(0)

    dataBUF.write("\n;;; CITIROC{0} {1} {2} ;;;\n".format(nCIT,IGAIN[nGain],ICH[nChannel]))
    hexDataBUF.write("\n;;; CITIROC{0} {1} {2} ;;;\n".format(nCIT,IGAIN[nGain],ICH[nChannel]))
    for c in intCIT[nCIT][nGain][nChannel]:
        dataBUF.write("{} ".format(c))
        hexDataBUF.write("{} ".format(hex(c)[2:].zfill(3)))

    if lastIteration:
        dataFileName = dataFileHead+fileSel[:fileSel.find(fNameHead)]+".txt"
        hexDataFileName = hexDataFileHead+fileSel[:fileSel.find(fNameHead)]+".txt"

        with open(dataFileName,"w") as dataFile,\
            open(hexDataFileName,"w") as hexDataFile:
                dataFile.write(dataBUF.getvalue())
                hexDataFile.write(hexDataBUF.getvalue())

    os.chdir(stDir)
    
    return 0

def saveMeansFile(nCIT,nGain,nChannel,fileSel,stDir,resDirName,parStr,intCIT,\
                  outAvg,outAvgErr,numEvt):
    if not os.path.exists(resDirName):
        os.mkdir(resDirName)
    os.chdir(resDirName)
    
    firstIteration = (nCIT == 0 and nGain == 0 and nChannel == 0)
    lastIteration = (nCIT == 1 and nGain == 1 and nChannel == 31)

    if firstIteration:
        meansBUF.truncate(0)
        meansBUF.seek(0)
        meansTxtBUF.truncate(0)
        meansTxtBUF.seek(0)
        meansBUF.write(";;; {} ;;;".format(parStr))
        meansTxtBUF.write(";;; {} ;;;\n;;;\tCITIROC\tGAIN\tCHANNEL\t   MEAN\t\t     ERR\t;;;\n".format(parStr))

    outAvg[nCIT][nGain][nChannel] = np.average(intCIT[nCIT][nGain][nChannel])
    stdDev = np.std(intCIT[nCIT][nGain][nChannel])
    outAvgErr[nCIT][nGain][nChannel] = stdDev#/np.sqrt(numEvt)

    meansBUF.write("\n;;; CITIROC{0} {1} {2} ;;;\n{3:.3f} {4:.3f}".format(nCIT,\
                    IGAIN[nGain],\
                    ICH[nChannel],
                    outAvg[nCIT][nGain][nChannel],\
                    outAvgErr[nCIT][nGain][nChannel]))
    
    meansTxtBUF.write("\t{0}\t{1}\t{2}\t{3:8.1f}\t{4:8.1f}\n".format(nCIT,\
                    IGAIN[nGain],\
                    ICH[nChannel],
                    outAvg[nCIT][nGain][nChannel],\
                    outAvgErr[nCIT][nGain][nChannel]))
    if lastIteration:
        with open(meansFileHead+fileSel[:fileSel.find(fNameHead)]+".dat","w") as meansFile,\
            open(meansFileHead+fileSel[:fileSel.find(fNameHead)]+".txt","w") as meansTxtFile:
                meansFile.write(meansBUF.getvalue())
                meansTxtFile.write(meansTxtBUF.getvalue())

    os.chdir(stDir)

def gauss(x, *p):
    A, mu, sigma = p
    return A*np.exp(-(x-mu)**2/(2.*sigma**2))

def multigauss(x,*p):
    multi=np.zeros_like(x)

    for i in range(0,len(p),3):
        A=p[i]
        mu=p[i+1]
        sigma=p[i+2]
        
        multi += gauss(x,A,mu,sigma)
    
    return multi

def adcToPC(cit,ch,g,adcVal,gainsDict):
    
    citOK = cit in adcToPCDict.keys()
    if citOK:
        gOK = g in adcToPCDict[cit].keys()
    else:
#        print(f"{cit} non presente!")
        return 0
    
    if gOK:
        chOK = ch in adcToPCDict[cit][g].keys()
        chGainsOK = ch in gainsDict[cit][g].keys()
    else:
#        print(f"{g} non presente!")
        return 0
    
    if chOK and chGainsOK:
        gainVal = gainsDict[cit][g][ch]
        gainValOK = gainVal in adcToPCDict[cit][g][ch].keys()
    else:
#        print(f"{ch} non presente!")
        return 0
    
    if gainValOK:
        p = adcToPCDict[cit][g][ch][gainVal]
        return (adcVal-p['interc'])/p['adcPerPC']
    else:
#        print(f"{gainVal} non presente!")
        return 0
#    if CIT[cit] == 0:
#        return (adcVal-122)/52.15
#    elif CIT[cit] == 1:
##        return (adcVal-155)/27.75
#        return (adcVal-112)/25.19 #le ultime misure danno questi valori
#    else:
#        return 0

def adcToPE(cit,ch,g,adcVal,gainsDict): #### ESTENDERE PER TUTTI I CANALI E PER TUTTI I PMT!!!
    pcVal = adcToPC(cit,ch,g,adcVal,gainsDict)
    
    if CIT[cit] == 0:
        uscita = "anodo"
    elif CIT[cit] == 1:
        uscita = "dinodo"
    
    if ch in PMTraw[cit].keys() and PMTraw[cit][ch] in PMTGain[900].keys():
        pcForPE = 1.6e-19 * PMTGain[900][PMTraw[cit][ch]][uscita]
        return (pcVal*1e-12)/pcForPE
    else:
#        print(f"{PMTChannel[ch]} non presente!")
        return 0

def savePlot(startDir,resDirName,citArray,cit,gain,channel,numEvt,gainsDict,evtPass,
             histParams = None,hist2D = None, gaussFitGuess = None,
             multiGaussFitGuess = None):
    if not os.path.exists(resDirName):
        os.mkdir(resDirName)
    os.chdir(resDirName)
    
    if (-1 not in cit) or (-1 not in gain) or (-1 not in channel):

        for c in cit:
            if not os.path.exists(c):
                os.mkdir(c)
            os.chdir(c)

            for g in gain:
                if not os.path.exists(g):
                    os.mkdir(g)
                os.chdir(g)

                if hist2D is not None:
                    for chCouple in hist2D:
                        chA = chCouple[0]
                        chB = chCouple[1]
                        chAbits = citArray[CIT[c]][GAIN[g]][chA]
                        chBbits = citArray[CIT[c]][GAIN[g]][chB]
                        chAint = [int(a,2) for a in chAbits]
                        chBint = [int(b,2) for b in chBbits]

                        plt.rc('axes', axisbelow=True)

                        plt.grid(which='both')
                        plt.minorticks_on()

                        plt.ticklabel_format(style='sci',scilimits=(0,1))
                        
                        plt.xlim((0,500))
                        plt.ylim((0,500))
                        plt.xticks(np.arange(0,550,50))#,rotation=90)
                        plt.yticks(np.arange(0,550,50))

                        plt.xlabel(f"ADC {PMT[c][ICH[chA]]}")
                        plt.ylabel(f"ADC {PMT[c][ICH[chB]]}")

                        if (histParams is not None) and ('binsWidth' in histParams):
                            hist2dBinsWidth = histParams['binsWidth']
                        else:
                            hist2dBinsWidth = 60

                        binsSize = np.arange(0, 4096 + hist2dBinsWidth, 
                                                 hist2dBinsWidth)

                        H, xedges, yedges = np.histogram2d(chAint,chBint,
                                                           bins=binsSize)
                        
                        H = np.ma.masked_where(H < 0.05, H)
                        
                        colMap = cm.get_cmap("rainbow")
                        colMap.set_bad(color='white')

                        im = plt.imshow(H,cmap=colMap, interpolation='nearest', origin='low',
                                   extent=[xedges[0], xedges[-1], yedges[0], yedges[-1]])

                        cb = plt.colorbar(im)
                        cb.formatter.set_powerlimits((0, 0))
                        cb.update_ticks()
#                        plt.plot(np.arange(0,4201,1),np.arange(0,4201,1))
                        plt.savefig(f"hist2d_{PMTraw[c][ICH[chA]]}_vs_"
                                    f"{PMTraw[c][ICH[chB]]}.jpg",
                                    bbox_inches = 'tight', dpi=300)
                        plt.clf()

                for ch in channel:
                    x = np.arange(0,numEvt,1)
                    y = []
                    
                    chStr = f"{CH[ch]:02d}"

                    for n in citArray[CIT[c]][GAIN[g]][CH[ch]]:
                        unit = 'adc'
                        if histParams != None:
                            if 'histUnits' in histParams:
                                unit = histParams['histUnits'].lower()
                            else:
                                unit = 'adc'
                            
                        if unit == 'pc':
                            y.append(adcToPC(c,chStr,g,
                                            int(n,2),gainsDict))
                            unitString = "Q (pC)"
                        elif unit == 'pe':
                            y.append(adcToPE(c,chStr,g,
                                             int(n,2),gainsDict))
                            unitString = "Num. fotoelettroni"
                        else:
                            y.append(int(n,2))
                            unitString = "Conteggi ADC"

                    plt.ylim((0,4096))
                    plt.xlim((0,numEvt))
                    plt.xlabel("N° evento\nCITIROC{} {} {}".format(CIT[c],g,ch))
                    plt.ylabel("Conteggi ADC")
                    plt.yticks(np.arange(0,4096,200))
                    plt.xticks(np.arange(0,numEvt,numEvt/10))#,rotation=90)
                    plt.ticklabel_format(style='sci', axis='x', scilimits=(0, 0))
                    
                    plt.minorticks_on()
                    plt.grid(linestyle='-')
                    
                    plt.plot(x,y)
                    plt.savefig("{}-{}.jpg".format(resDirName,ch), bbox_inches = 'tight', dpi=300)
                    plt.clf()

                    fitParams = ""
                    
                    if histParams != None:                        
                        ### aggiungere gestione eccezioni!
                        histBinsWidth = histParams['binsWidth']

                        if unit == 'pc':
                            binsSize = np.arange(0, 400 + histBinsWidth, 
                                                 histBinsWidth)
                        elif unit == 'pe':
                            binsSize = np.arange(0, 2500 + histBinsWidth,
                                                 histBinsWidth)
                        else:
                            binsSize = np.arange(min(y), max(y) + histBinsWidth, 
                                                 histBinsWidth)

                        histColor = histParams['color']

                        histRes = plt.hist(y,bins=binsSize,color=histColor)
                        yAvg = np.average(y)

                        if len(histRes[0]) == 0:
                            maxHistRes = numEvt
                        else:
                            maxHistRes = max(histRes[0])
                        
                        if 'xlim' in histParams:
                            if (type(histParams['xlim']) is tuple 
                                     and len(histParams['xlim']) == 2):
                                histXLim = histParams['xlim']
                            elif type(histParams['xlim']) is int:
                                histXLim = (yAvg-histParams['xlim'],
                                            yAvg+histParams['xlim'])
                            else:
                                raise Exception("Errore in histParams['xlim']!")
                        else:
                            histXLim = (min(histRes[1]),max(histRes[1]))

                        if 'xpass' in histParams:
                            histXPass = histParams['xpass']
                        else:
                            histXPass = None

                        if 'ylim' in histParams:
                            if (type(histParams['ylim']) is tuple and 
                                     len(histParams['ylim']) == 2):
                                histYLim = histParams['ylim']
                            elif type(histParams['ylim']) is int:
                                histYLim = (0,maxHistRes+histParams['ylim'])
                            else:
                                raise Exception("Errore in histParams['ylim']!")
                        else:
                            histYLim = (0,max(histRes[0])+int(max(histRes[0])/10))

                        if 'ypass' in histParams:
                            histYPass = histParams['ypass']
                        else:
                            histYPass = None

                        plt.minorticks_on()
                        plt.grid(linestyle='-',which='both')
                        plt.ticklabel_format(style='sci',scilimits=(0,2))

                        if 'ylog' in histParams and histParams['ylog'] is True:
                            plt.yscale("log")

                        if 'xlog' in histParams and histParams['xlog'] is True:
                            plt.xscale("log")

                        if histXLim is not None:
                            plt.xlim(histXLim)
                            if histXPass is not None:
                                plt.xticks(np.arange(*histXLim,histXPass))#,rotation=90)
                        if histYLim is not None:
                            plt.ylim(histYLim)
                            if histYPass is not None:
                                plt.yticks(np.arange(*histYLim,histYPass))

                        plt.xlabel(f"{unitString} \nCITIROC{CIT[c]} {g} {ch}")# ({PMT[c][ch]})")
                        plt.ylabel("N° occorrenze")
                        
                        gaussFIT = histParams['gaussFIT']
                        
                        hVals = histRes[0]
                        
                        bins = histRes[1]

                        sigBins = []
                        sigHist = []
                        
                        if 'fitRange' in histParams:
                            fitMin = histParams['fitRange'][0]
                            fitMax = histParams['fitRange'][1]
                        else:
                            if unit == 'pe':
                                fitMin = 0
                                fitMax = 2500
                            elif unit == 'pc':
                                fitMin = 0
                                fitMax = 400
                            else:
                                fitMin = 0
                                fitMax = 4100
                            
                        for i,h in enumerate(hVals):
                            if bins[i] > fitMin and bins[i] < fitMax:
                                sigBins.append(bins[i])
                                sigHist.append(h)
                        
#                        print(f"sigBins[0]={sigBins[0]} sigBins[-1]={sigBins[-1]}")
#                        print(f"sigHist[0]={sigHist[0]} sigHist[-1]={sigHist[-1]}")
                        
                        for i,h in enumerate(sigHist):
                            if h == max(sigHist):
                                u0 = sigBins[i]

                        xFitBins = [(sigBins[i+1]+sigBins[i])/2 for i in range(len(sigBins)-1)]

                        if gaussFIT is True:

                            print(f"u0={u0}, h0={min(sigBins)} h1={max(sigBins)}")
                            if gaussFitGuess is not None:
                                popt,pcov = curve_fit(gauss, xFitBins,sigHist[:-1],p0=gaussFitGuess)
                                perr = np.sqrt(np.diag(pcov))
                            else:
                                popt,pcov = curve_fit(gauss, xFitBins,sigHist[:-1],p0=[maxHistRes,u0, 0.5])
                                perr = np.sqrt(np.diag(pcov))

#                            xFitG = np.arange(0,4096,1)

#                            yfitG = gauss(xFitG,*popt)
                            if unit == 'pc':
                                xFitG = np.arange(0,400,0.1)
                                yfitG = gauss(xFitG,*popt)
                            elif unit == 'pe':
                                xFitG = np.arange(0,2500,1)
                                yfitG = gauss(xFitG,*popt)
                            else:
                                yfitG = gauss(xFitBins,*popt)

                            print(f"canale {ch} perr={perr}")
                            
#                            yChi = gauss(xFitBins,*popt)
                            
#                            dof = len(xFitBins)-3
                            
#                            deltaY = sigHist[:-1] - yChi

#                            chi2 = np.sum((deltaY**2)/yChi)/dof
                            
                            legStr = (f"$\mu={popt[1]:.2f}$\n"
                                      f"$\sigma={popt[2]:.2f}$\n"
#                                      f"$\~{{\chi}}^2={chi2:.2f}$\n"
                                      f"#evt = {numEvt}\n"
                                      f"$\Delta\mu={perr[1]:.2f}$\n"
                                      f"$\Delta\sigma={perr[2]:.2f}$")
                            
                            fitParams = (f"{popt[1]} {popt[2]} "
                                         f"{perr[1]} {perr[1]}\n")
                            
                            plt.text(histXLim[-1],histYLim[-1],legStr, 
                                     bbox=dict(facecolor='white', alpha=1),
                                     horizontalalignment='right',
                                     verticalalignment='top')
                            if unit == 'adc':
                                plt.plot(xFitBins,yfitG,'g')
                            else:
                                plt.plot(xFitG,yfitG,'g')
                        
                        multiGaussFit = histParams['multiGaussFit']
                        
                        if (multiGaussFit is not None) and (multiGaussFit is True):
                            
                            legStr = ""
                            
                            if multiGaussFitGuess is not None:
                                popt,pcov = curve_fit(multigauss, xFitBins,
                                                      sigHist[:-1],
                                                      p0=multiGaussFitGuess)
                                perr = np.sqrt(np.diag(pcov))
                            else:
                                popt,pcov = curve_fit(multigauss, xFitBins,
                                                      sigHist[:-1],
                                                      p0=[1,1,1,1,1,1])
                                perr = np.sqrt(np.diag(pcov))
                                
                            xFitG = np.arange(0.0,4096.0,1.0)
                            yfitG = multigauss(xFitG,*popt)

                            peakNum = 0

                            for i in range(0,len(popt),3):
                                
                                peakNum += 1
                                
                                legStr += (f"$\mu_{peakNum}={popt[i+1]:.2f}$\n"
                                          f"$\sigma_{peakNum}={popt[i+2]:.2f}$\n")
    #                                      f"$\~{{\chi}}^2={chi2:.2f}$\n"
#                                          f"$\Delta\mu={perr[1]:.2f}$\n"
#                                          f"$\Delta\sigma={perr[2]:.2f}$\n\n")
                            
#                            fitParams = (f"{popt[1]:.2f} {popt[2]:.2f} "
#                                         f"{perr[1]:.2f} {perr[1]:.2f}\n")
                                pi = (popt[i],popt[i+1],popt[i+2])
                                ySingle = gauss(xFitG,*pi)

                                plt.plot(xFitG,ySingle,'g')
                            
                            legStr += f"#evt = {numEvt}"

                            plt.text(histXLim[-1],histYLim[-1],legStr, 
                                     bbox=dict(facecolor='white', alpha=1),
                                     horizontalalignment='right',
                                     verticalalignment='top')

#                            fitParams = (f"{popt[1]:.2f} {popt[2]:.2f} "
#                                         f"{perr[1]:.2f} {perr[1]:.2f}\n")
                            
#                            plt.plot(xFitG,yfitG,'g')
                        
                        if unit == 'adc':
                            unitHistName = "adcUnit"
                        elif unit == 'pc':
                            unitHistName = "pCUnit"
                        else:
                            unitHistName = "peUnit"
                        
                        plt.savefig(f"hist-{resDirName}-{ch}-{unitHistName}.jpg", 
                                    bbox_inches = 'tight', dpi=300)
                        plt.clf()

                os.chdir("..")
                
            os.chdir("..")
            
            oldDir = os.getcwd()
            os.chdir(startDir)

            with open("gaussFITParams.dat","a") as gff:
                gff.write(fitParams)

            os.chdir(oldDir)

            
    else:
        raise Exception("Errore nella selezione!")

    os.chdir(startDir)

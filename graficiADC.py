# -*- coding: utf-8 -*-
"""
Created on Mon May  6 11:38:36 2019

@author: Marco
"""

import analisiLib as al
from serialeLib import unitPattern,prompt,InCALIBGainToGainBits
from collections import defaultdict
import numpy as np
import os
import sys
import re
import matplotlib.pyplot as plt

#sys.path.insert(0,"../pmtPulse")
#from plotPulseData import pulseTtoQ

validDirPattern = "(?i){resDir}[\w]+(-\(?[\d]+{unitP}\)?)*".format(resDir = al.resDirHead,\
                                                                   unitP = unitPattern)

startDir = os.getcwd()

filesInDir = os.listdir()

dataDirs = []

vImp = []
vImpErr = []
widthImp = []
widthImpErr = []
distImp = []
holdDelay = []
gainSet = defaultdict(list)
gainSetErr = defaultdict(list)

meansV = []

#ledTOpmtV = {
#        41.0 : 50,
#        42.0 : 78,
#        43.0 : 151,
#        43.5 : 220,
#        44.0 : 326,
#        44.5 : 468,
#        45.0 : 665,
#        45.5 : 909,
#        46.0 : 1260,
#        46.5 : 1589,
#        47.0 : 1982,
#        47.5 : 2438,
#        48.0 : 2895,
#        48.5 : 3303,
#        49.0 : 3695,
#        49.5 : 4054,
#        50.0 : 4405,
#        50.5 : 4752,
#        51.0 : 5072,
#        51.5 : 5361,
#        52.0 : 5629,
#        52.5 : 5856,
#        53.0 : 6048
#        }

for f in filesInDir:
    isDirValid = re.match(validDirPattern,f)
    
    if os.path.isdir(f) and isDirValid is not None:
        dataDirs.append(f)

for d in dataDirs:
    vImpVal = 0
    vErrImpVal = 0
    
    
    os.chdir(d)
    
    meansFileName = al.meansFileHead+d[len(al.resDirHead):]+".dat"
    
    try:
        with open(meansFileName,'r') as meansFile:
            paramString = meansFile.readline()
            
            mvString = re.search("V=[\d]+\.[\d]+mv",paramString)
            mvErrString = re.search("Verr=[\d]+\.[\d]+mv",paramString)
            nsString = re.search("T=[\d]+\.[\d]+ns",paramString)
            nsErrString = re.search("Terr=[\d]+\.[\d]+mv",paramString)
#            gString = re.search("G=[\d]+\.[\d]+g",paramString)
#            gErrString = re.search("Gerr=[\d]+\.[\d]+g",paramString)
            hgString = re.search("HG=[\d]+\.[\d]+g",paramString)
            hgErrString = re.search("HGerr=[\d]+\.[\d]+g",paramString)
            lgString = re.search("LG=[\d]+\.[\d]+g",paramString)
            lgErrString = re.search("LGerr=[\d]+\.[\d]+g",paramString)
            distImpString = re.search("impDist=[\d]+\.[\d]+ns",paramString)
            holdDelayString = re.search("holdDelay=[\d]+ns",paramString)

            if mvString is not None: #### fare una unica funzione per questo!!!!!
                vImpValStr = re.search("[\d]+\.[\d]",mvString.group())
                if vImpValStr is not None:
                    vImpVal = float(vImpValStr.group())
                    vImp.append(vImpVal)
                    
            if mvErrString is not None:
                vErrImpValStr = re.search("[\d]+\.[\d]",mvErrString.group())
                if vErrImpValStr is not None:
                    vErrImpVal = float(vErrImpValStr.group())
                    vImpErr.append(vErrImpVal)
            
            if nsString is not None:
                nsImpValStr = re.search("[\d]+\.[\d]",nsString.group())
                if nsImpValStr is not None:
                    nsImpVal = float(nsImpValStr.group())
                    widthImp.append(nsImpVal)
                    
            if nsErrString is not None:
                nsErrImpValStr = re.search("[\d]+\.[\d]",nsErrString.group())
                if nsErrImpValStr is not None:
                    nsErrImpVal = float(nsErrImpValStr.group())
                    widthImpErr.append(nsErrImpVal)
            
            if hgString is not None and lgString is not None:
                hgValStr = re.search("[\d]+\.[\d]+",hgString.group())
                lgValStr = re.search("[\d]+\.[\d]+",lgString.group())
                if hgValStr is not None and lgValStr is not None:
                    hgVal = float(hgValStr.group())
                    lgVal = float(lgValStr.group())
                    gainSet["hg"].append(hgVal)
                    gainSet["lg"].append(lgVal)
                    # gainSet["hg"].append(int(InCALIBGainToGainBits[hgVal],2)) #debug!
                    # gainSet["lg"].append(int(InCALIBGainToGainBits[lgVal],2)) #debug!

            if hgErrString is not None and lgErrString is not None:
                hgErrValStr = re.search("[\d]+\.[\d]",hgErrString.group())
                lgErrValStr = re.search("[\d]+\.[\d]",lgErrString.group())
                if hgErrValStr is not None and lgErrValStr is not None:
                    hgErrVal = float(hgErrValStr.group())
                    lgErrVal = float(lgErrValStr.group())
                    gainSetErr["hg"].append(hgErrVal)
                    gainSetErr["lg"].append(lgErrVal)

            if distImpString is not None:
                distImpValStr = re.search("[\d]+\.[\d]",distImpString.group())
                if distImpValStr is not None:
                    distImpVal = float(distImpValStr.group())
                    distImp.append(distImpVal)
                    
            if holdDelayString is not None:
                holdDelayValStr = re.search("[\d]+",holdDelayString.group())
                if holdDelayValStr is not None:
                    holdDelayVal = float(holdDelayValStr.group())
                    holdDelay.append(holdDelayVal)

            meansFromFile = np.genfromtxt(meansFile,comments=';',delimiter=' ',dtype=[float,float])
            meansV.append(meansFromFile)

    except Exception as e:
        os.chdir(startDir)
        sys.exit(e)

    os.chdir("..")

os.chdir(startDir)

numOfV = len(vImp)

meansCIT = np.ndarray(shape = (2,2,32,numOfV), dtype = float)
errsCIT = np.ndarray(shape = (2,2,32,numOfV), dtype = float)
meansPerV = np.ndarray(shape = (numOfV,2,2,32), dtype = float) #probabilmente c'è un modo migliore
errsPerV = np.ndarray(shape = (numOfV,2,2,32), dtype = float)  #ad esempio dovrebbe essere possibile invertire le "colonne"

for i in range(numOfV):
    for nCIT in range(0,2):
        for nGain in range(0,2):
            for nChannel in range(0,32):
                
                citIndex = nChannel+(32*nGain)+(64*nCIT)
                
                meansCIT[nCIT][nGain][nChannel][i] = meansV[i][citIndex][0]
                errsCIT[nCIT][nGain][nChannel][i] = meansV[i][citIndex][1]
                
                meansPerV[i][nCIT][nGain][nChannel] = meansV[i][citIndex][0]
                errsPerV[i][nCIT][nGain][nChannel] = meansV[i][citIndex][1]
                
                
citiroc,gain,channel = al.plotPrompt()

plotDirName = input("Inserire il nome della cartella in cui salvare i grafici: ")

xType = prompt("Inserire la grandezza da riportare sulle ascisse ",\
               "mv","q","ns","hg","lg","distImp","holdDelay","ledns",default="mv")

cutOK = False

while cutOK is False:
    cutOffInput = input("Inserire il range di valori per x in cui effettuare il fit (valori interi senza unità di misura separati da '-', "
                        "'*' per non effettuare il fit): ")
    cutOffMatch = re.match("^[\d]+-[\d]+$",cutOffInput)
    if cutOffMatch is not None:
        cutOffMin,cutOffMax = cutOffMatch.group().split('-')
        cutOK = True
    elif cutOffMatch is None and cutOffInput == "*":
        cutOK = True
    else:
        cutOK = False

if not os.path.exists(plotDirName):
    os.mkdir(plotDirName)
os.chdir(plotDirName)

if (-1 not in citiroc) or (-1 not in gain) or (-1 not in channel):
    for c in citiroc:
        if not os.path.exists(c):
            os.mkdir(c)
        os.chdir(c)
        
        for g in gain:
            if not os.path.exists(g):
                os.mkdir(g)
            os.chdir(g)
            
            for ch in channel:
                adcVal = []
                xFitVal = []

                if xType == "mv":
                    xVal = vImp
                    othersParamStr = f"\n T = {nsImpVal}ns HG = {hgVal} LG = {lgVal}"
                    if cutOffInput != "*":
                        xStr = "Vimp(mV)\nADC=({0:.2f}±{5:.2f}) Vimp + ({1:.1f}±{6:.1f})\nCITIROC {2} {3} {4}"
                    else:
                        xStr = "Vimp(mV)\nCITIROC {2} {3} {4}"

                    xStr += othersParamStr

                elif xType == "q":
                    xVal = [pulseTtoQ(w)*0.475 for w in widthImp] #divido per 20 e moltiplico per 9.5 perchè c'è il fattore di attenuazione in ingresso e di guadagno del citiroc
                    
                    othersParamStr = f"\n T = {nsImpVal}ns HG = {hgVal} LG = {lgVal}"
                    if cutOffInput != "*":
                        xStr = "Q(pC)\nADC=({0:.2f}±{5:.2f}) Q + ({1:.1f}±{6:.1f})\nCITIROC {2} {3} {4}"
                    else:
                        xStr = "Q(pC)\nCITIROC {2} {3} {4}"

                    xStr += othersParamStr
                
                
                elif xType == "ns":
                    xVal = widthImp
                    othersParamStr = f"\n V = {vImpVal}mV HG = {hgVal} LG = {lgVal}"
                    if cutOffInput != "*":
                        xStr = "Timp(ns)\nADC=({0:.1f}±{5:.1f}) Timp + ({1:.1f}±{6:.1f})\nCITIROC {2} {3} {4}"
                    else:
                        xStr = "Timp(ns)\nCITIROC {2} {3} {4}"
                    
                    xStr += othersParamStr

                elif xType == "hg":
                    xVal = gainSet["hg"]
                    othersParamStr = f"\n V = {vImpVal}mV T = {nsImpVal}ns"
                    if cutOffInput != "*":
                        xStr = "HG Gain\nADC=({0:.1f}±{5:.1f}) Gain + ({1:.1f}±{6:.1f})\nCITIROC {2} {3} {4}"
                    else:
                        xStr = "HG Gain\nCITIROC {2} {3} {4}"
                    
                    xStr += othersParamStr

                elif xType == "lg":
                    xVal = gainSet["lg"]
                    othersParamStr = f"\n V = {vImpVal}mV T = {nsImpVal}ns"
                    if cutOffInput != "*":
                        xStr = "LG Gain\nADC=({0:.1f}±{5:.1f}) Gain + ({1:.1f}±{6:.1f})\nCITIROC {2} {3} {4}"
                    else:
                        xStr = "LG Gain\nCITIROC {2} {3} {4}"
                    
                    xStr += othersParamStr

                elif xType == "distImp":
                    xVal = distImp
                    othersParamStr = f"\n V = {vImpVal}mV HG = {hgVal} LG = {lgVal} T = {nsImpVal}ns"
                    if cutOffInput != "*":
                        xStr = "distT(ns)\nADC=({0:.1f}±{5:.1f}) distT + ({1:.1f}±{6:.1f})\nCITIROC {2} {3} {4}"
                    else:
                        xStr = "distT(ns)\nCITIROC {2} {3} {4}"
                    
                    xStr += othersParamStr
                    
                elif xType == "holdDelay":
                    xVal = holdDelay
                    othersParamStr = f"\n V = {vImpVal}mV HG = {hgVal} LG = {lgVal} T = {nsImpVal}ns"
                    if cutOffInput != "*":
                        xStr = "holdDelay(ns)\nADC=({0:.1f}±{5:.1f}) distT + ({1:.1f}±{6:.1f})\nCITIROC {2} {3} {4}"
                    else:
                        xStr = "holdDelay(ns)\nCITIROC {2} {3} {4}"
                    
                    xStr += othersParamStr

                elif xType == "ledns":
                    xVal = [ledTOpmtV[w] for w in widthImp]
                    othersParamStr = ""#f"\n V = {vImpVal}mV HG = {hgVal} LG = {lgVal}"
                    if cutOffInput != "*":
                        xStr = "$V_{{PMT}}$ (mV)\nADC=({0:.1f}±{5:.1f}) $V_{{PMT}}$ + ({1:.1f}±{6:.1f})\nCITIROC {2} {3} {4}"
                    else:
                        xStr = "$V_{{PMT}}$\nCITIROC {2} {3} {4}"
                    
                    xStr += othersParamStr

                else:
                    raise Exception("Tipo errato per le ascisse!")

                xyDataWithErr = list(zip(xVal,
                                     meansCIT[al.CIT[c]][al.GAIN[g]][al.CH[ch]],
                                     errsCIT[al.CIT[c]][al.GAIN[g]][al.CH[ch]]))
#                else:
#                    xyDataWithErr = []
#
#                    for i,x in enumerate(xVal):
#                        if x[0] <= 500.0:
#                            xyDataWithErr.append([x[1],meansCIT[al.CIT[c]][al.GAIN[g]][al.CH[ch]][i],
#                                                 errsCIT[al.CIT[c]][al.GAIN[g]][al.CH[ch]][i]]) 
                
                xyDataWithErr.sort()
                
                xSorted = []
                ySorted = []
                yErrSorted = []
                
                for x,y,err in xyDataWithErr:
                    xSorted.append(x)
                    ySorted.append(y)
                    yErrSorted.append(err)
                
                if cutOffInput != "*":
                    xyToFit = [[i,v] for i,v in enumerate(xVal) 
                            if v < float(cutOffMax) and v > float(cutOffMin)]
                    for x in xyToFit:
                        xFitVal.append(x[1])
                        adcVal.append(meansCIT[al.CIT[c]][al.GAIN[g]][al.CH[ch]][x[0]])
                    
                    fit = np.polyfit(xFitVal,adcVal,1,cov=True)
                    fitFunc = np.poly1d(fit[0])
                    
                    fitErr = np.sqrt(np.diag(fit[1]))
                    
                    formatTuple = (fit[0][0],fit[0][1],al.CIT[c],g,ch,
                                   fitErr[0],fitErr[1])
                    plotTuple = (xSorted,ySorted,'r.',xVal,fitFunc(xVal),'g')

                else:
                    formatTuple = (0,0,al.CIT[c],g,ch,
                                   0,0)
                    plotTuple = (xSorted,ySorted,'r.')
                
#                plt.xlim((0,np.amax(xVal)))
#                plt.xlim((40,50))
                if xType != "distImp":
                     plt.ylim((200,1100))
#                    plt.ylim((1000,3000))
                else:
                    plt.ylim((0,500))

                plt.xlabel(xStr.format(*formatTuple))

                plt.ylabel("Conteggi ADC")

                #plt.errorbar(xSorted,ySorted,yerr=yErrSorted,fmt='none')

                plt.minorticks_on()
                plt.grid(linestyle='-', which = 'both')
                
                plt.plot(*plotTuple,markersize=2)
                plt.savefig(f"{plotDirName}-{ch}.jpg", 
                            bbox_inches = 'tight', dpi=300)
                plt.clf() 

                parStr = othersParamStr[1:]
                dataFileName = f"plotData{parStr.replace(' ','_')}.dat"

                with open(dataFileName,"w") as dataFile:
                    dataFile.write(f";;; CIT{al.CIT[c]} {g} {ch}"
                                   f" {parStr}\n")
                    dataFile.write(";;; xVal Means yErr\n\n")
                    for x,y,err in xyDataWithErr:
                        dataFile.write(f"{x} {y} {err}\n")

            os.chdir("..")
            
        os.chdir("..")

    os.chdir("..")

else:
    raise Exception("Errore nella selezione!")
    
os.chdir(startDir)


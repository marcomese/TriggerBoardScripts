# -*- coding: utf-8 -*-

import os
import matplotlib.pyplot as plt
import numpy as np
from lmfit.models import StepModel,PolynomialModel
import re

numericPattern = "([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)*)"
meanPattern = f"\s*center:\s*{numericPattern}\s*"
fwhmPattern = f"\s*fwhm:\s*{numericPattern}\s*"
sigmaPattern = f"\s*sigma:\s*{numericPattern}\s*"
dirNamePattern = f"(-)?{numericPattern}ns?{numericPattern}?(_2)?"

meanRegex = re.compile(meanPattern)
fwhmRegex = re.compile(fwhmPattern)
sigmaRegex = re.compile(sigmaPattern)
dirNameRegex = re.compile(dirNamePattern)

startDir = os.getcwd()

# os.chdir("D:/TB3/triggerBoardLibs/trToSIG/holdDel127")
os.chdir("D:/TB_FM/triggerBoardLibs/trgSigCalib")

dataDir = os.getcwd()

pdstRange = (-1,None)
topRange = (0,4)

dirsVal = {}
for d in os.scandir():
    if d.is_dir() and (regexRes := dirNameRegex.findall(d.name)):
        sign = regexRes[0][0]
        intVal = regexRes[0][1]
        decVal = '0' if regexRes[0][2] == '' else regexRes[0][2]
        tVal = f"{sign}{intVal}.{decVal}"
        dirsVal.update({d.name:float(tVal)})

tAdcData = []
for d,tVal in dirsVal.items():
    os.chdir(d)
    
    for f in os.scandir():
        if "analisi" in f.name and f.is_dir():
            os.chdir(f)
            break

    noMoreDir = False
    while noMoreDir is False:
        dirNum = len(os.listdir())
        for ff in os.scandir():
            if not ff.is_dir():
                dirNum -= 1
        
        if dirNum == 0:
            noMoreDir = True
        else:
            os.chdir(ff)
    
    with open("fitReport.dat") as HGfile:
        hgFitData = HGfile.read()
        
        hgMean = meanRegex.findall(hgFitData)[0]
        hgErr = sigmaRegex.findall(hgFitData)[0]

        tAdcData.append((float(tVal),
                        float(hgMean),
                        float(hgErr)))

        os.chdir(dataDir)

os.chdir(dataDir)

tAdcData.sort()

tAdcData = np.asarray(tAdcData)

t = tAdcData[:,0]
adc = tAdcData[:,1]
adcErr = tAdcData[:,2]

pdst = np.mean(adc[pdstRange[0]:pdstRange[1]])
top = np.mean(adc[topRange[0]:topRange[1]])

plt.xlabel(r"$T_{sig}-T_{trig}$ (ns)")
plt.ylabel("<ADC>")
plt.grid(which='both')
plt.minorticks_on()

plt.plot(t,adc,'r.')
plt.errorbar(t, adc, yerr=adcErr, fmt='none')
plt.hlines(y=pdst,xmin=min(t),xmax=max(t),color='r',label='pedestal')
plt.hlines(y=top,xmin=min(t),xmax=max(t),color='g',label='peak')
plt.axvline(x=0,ymin=0,ymax=1,color='black')

plt.legend(loc='lower left')

plt.savefig("timingTrgToSig.png",dpi=150,bbox_inches='tight')

os.chdir(startDir)
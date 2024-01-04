# -*- coding: utf-8 -*-
"""
Created on Sat Nov 13 14:47:46 2021

@author: mames
"""

import os
import matplotlib.pyplot as plt
import numpy as np
from lmfit.models import StepModel,PolynomialModel
import re

hgFitStart = 0
hgFitStop = -9

lgFitStart = 0
lgFitStop = None

numDegHG = 3
numDegLG = 4

numericPattern = "([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)*)"
meanPattern = f"\s*center:\s*{numericPattern}\s*"
fwhmPattern = f"\s*fwhm:\s*{numericPattern}\s*"
sigmaPattern = f"\s*sigma:\s*{numericPattern}\s*"

meanRegex = re.compile(meanPattern)
fwhmRegex = re.compile(fwhmPattern)
sigmaRegex = re.compile(sigmaPattern)

startDir = os.getcwd()

os.chdir("D:/TB3/triggerBoardLibs/misureBologna/acquisizioniLED")

dataDir = os.getcwd()

dirsVal = [int(d.name.split("mv")[0]) for d in os.scandir() if d.is_dir()]
dirsVal.sort()
dirs = [f"{d}mv" for d in dirsVal]

amplAdcData = np.empty((len(dirs),7))
for i,d in enumerate(dirs):
    amplVal = d.split("mv")[0]

    os.chdir(d)
    
    with open("fitReportHG.dat") as HGfile, open("fitReportLG.dat") as LGfile:
        hgFitData = HGfile.read()
        lgFitData = LGfile.read()
        
        hgMean = meanRegex.findall(hgFitData)[0]
        lgMean = meanRegex.findall(lgFitData)[0]
        hgFwhm = fwhmRegex.findall(hgFitData)[0]
        lgFwhm = fwhmRegex.findall(lgFitData)[0]
        hgSigma = sigmaRegex.findall(hgFitData)[0]
        lgSigma = sigmaRegex.findall(lgFitData)[0]

        amplAdcData[i] = [float(amplVal),
                          float(hgMean),
                          float(hgFwhm),
                          float(lgMean),
                          float(lgFwhm),
                          float(hgSigma),
                          float(lgSigma)]

    os.chdir(dataDir)

os.chdir(dataDir)

x = amplAdcData[:,0]
yHG = amplAdcData[:,1]
yErrHG = amplAdcData[:,2]
ySigmaHG = amplAdcData[:,5]
yLG = amplAdcData[:,3]
yErrLG = amplAdcData[:,4]
ySigmaLG = amplAdcData[:,6]

hgModel = StepModel(form='logistic')
lgModel = PolynomialModel(degree=numDegLG)

xToFitHG = x[hgFitStart:hgFitStop]
yToFitHG = yHG[hgFitStart:hgFitStop]
ySigmaFitHG = ySigmaHG[hgFitStart:hgFitStop]

xToFitLG = x[lgFitStart:lgFitStop]
yToFitLG = yLG[lgFitStart:lgFitStop]
ySigmaFitLG = ySigmaLG[lgFitStart:lgFitStop]

hgFitParams = hgModel.guess(data=yToFitHG,x=xToFitHG)
lgFitParams = lgModel.guess(data=yToFitLG,x=xToFitLG)

hgFitRes = hgModel.fit(nan_policy='omit',
                       x=xToFitHG,
                       weights=1/ySigmaFitHG,
                       data=yToFitHG,
                       params=hgFitParams)
lgFitRes = lgModel.fit(nan_policy='omit',
                       x=xToFitLG,
                       weights=1/ySigmaFitLG,
                       data=yToFitLG,
                       params=lgFitParams)

xFitHG = np.linspace(min(xToFitHG),max(xToFitHG),100000)
yFitHG = hgModel.func(xFitHG,**hgFitRes.best_values)
xFitLG = np.linspace(min(xToFitLG),max(xToFitLG),100000)
yFitLG = lgModel.func(xFitLG,**lgFitRes.best_values)

uncHG = hgFitRes.eval_uncertainty(sigma=3,x=xFitHG,data=yFitHG)
uncLG = lgFitRes.eval_uncertainty(sigma=3,x=xFitLG,data=yFitLG)

hgFitErr = np.sqrt(np.diag(hgFitRes.covar))
lgFitErr = np.sqrt(np.diag(lgFitRes.covar))

hgText = (f"$A = {hgFitRes.best_values['amplitude']:.0f} \pm {hgFitErr[0]:.0f}$\n"
          f"$\mu = {hgFitRes.best_values['center']:.0f} \pm {hgFitErr[1]:.0f}$\n"
          f"$\sigma = {hgFitRes.best_values['sigma']:.0f} \pm {hgFitErr[2]:.0f}$")

lgText = ''
for lgk,lgv in lgFitRes.best_values.items():
    i = int(lgk.split('c')[1])
    lgText += f"{lgk} = ${lgv:.1e} \pm {lgFitErr[i]:.2e}$"
    if i != numDegLG:
        lgText += '\n'

hgXLabel = f"$V_{{ampl}}$ (mV)\nADC = $A\cdot (1-(1+e^{{\\frac{{V-\mu}}{{\sigma}}}})^{{-1}})$"

lgXLabel = f"$V_{{ampl}}$ (mV)\nADC = $"
for i,lgk in enumerate(lgFitRes.best_values.keys()):
    if i == 0:
        factStr = '+'
    elif i == 1:
        factStr = '\cdot V_{{ampl}} +'
    elif i == numDegLG:
        factStr = f'\cdot V_{{ampl}}^{i}'
    else:
        factStr = f'\cdot V_{{ampl}}^{i} +'
    lgXLabel += f"{lgk}{factStr}"
lgXLabel += f"$"

ax = plt.gca()
plt.title("High Gain")
plt.xlabel(hgXLabel)
plt.ylabel("<ADC>")
plt.text(0.95,0.05,hgText,
          bbox=dict(facecolor='white', alpha=1),
          horizontalalignment='right',
          verticalalignment='bottom',
          transform=ax.transAxes)
plt.plot(x,yHG,'b.',
         xFitHG,yFitHG,'g-')
plt.fill_between(xFitHG,yFitHG-uncHG,yFitHG+uncHG,
                 color="#ABABAB")
plt.errorbar(x, yHG, yerr=yErrHG, fmt='none')
plt.grid()
plt.minorticks_on()
plt.savefig("HGfit.png",dpi=150,bbox_inches='tight')

plt.clf()

ax = plt.gca()
plt.title("Low Gain")
plt.xlabel(lgXLabel)
plt.ylabel("<ADC>")
plt.text(0.95,0.05,lgText,
          bbox=dict(facecolor='white', alpha=1),
          horizontalalignment='right',
          verticalalignment='bottom',
          transform=ax.transAxes)
plt.plot(x,yLG,'b.',
          xFitLG,yFitLG,'g-')
plt.fill_between(xFitLG,yFitLG-uncLG,yFitLG+uncLG,
                 color="#ABABAB")
plt.errorbar(x, yLG, yerr=yErrLG, fmt='none')
plt.grid()
plt.minorticks_on()
plt.savefig("LGfit.png",dpi=150,bbox_inches='tight')

with open("HGFitFunc.dat","w") as hgFunc, open("LGFitFunc.dat","w") as lgFunc:
    hgFunc.write("x,y,yErr\n")
    lgFunc.write("x,y,yErr\n")
    
    for x,y in zip(xFitHG,yFitHG):
        hgFunc.write(f"{x},{y},{hgFitRes.eval_uncertainty(sigma=3,x=x)[0]}\n")

    for x,y in zip(xFitLG,yFitLG):
        lgFunc.write(f"{x},{y},{lgFitRes.eval_uncertainty(sigma=3,x=x)[0]}\n")

os.chdir(startDir)
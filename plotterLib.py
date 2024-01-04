# -*- coding: utf-8 -*-
"""
Created on Thu Jun 24 22:47:28 2021

@author: Wizard
"""
import numpy as np
import matplotlib.pyplot as plt
import citSupportLib as csl
import os
from math import log10,floor
from itertools import product
from scipy.optimize import curve_fit,OptimizeWarning
from lmfit.models import (GaussianModel,PolynomialModel,
                          StepModel,Model,LognormalModel)
import re
from matplotlib.ticker import AutoMinorLocator,AutoLocator,MaxNLocator
import matplotlib.patches as mpl_patches
#import qConvLib as qc

colors = 'bgrcmy'

othersUnit = {'v':('ns','hg','lg','s'),
              't':('mv','hg','lg','s'),
              'h':('mv','ns','lg','s'),
              'l':('mv','ns','hg','s'),
              's':('mv','ns','hg','lg'),
              'q':('ns','hg','lg','s')}

expIndip = {'v':1e-3,
            't':1,
            'h':1,
            'l':1,
            's':1,
            'q':1e-3}

numericPattern = "([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)*)"
numericRegex = re.compile(numericPattern)

headerPattern = f"(v|t|hg|lg|ssh)\s*=\s*{numericPattern}"
headerRegex = re.compile(headerPattern)

plotTypes = "ebdc"
autoTypes = [f"{p[0]}{p[1]}" for p in product(plotTypes,['x','y'])]

calibPlotTypes = "vthlsq"
calibAutoTypes = [f"{p[0]}{p[1]}" for p in product(calibPlotTypes,['x','y'])]

logisParNames = {'amplitude':'A',
                 'center':'\mu',
                 'sigma':'\sigma'}

def moyalFunc(x,A,mu,sigma):
    xx = (x-mu)/sigma

    coeff = A/np.exp(-0.5)
    
    numrt = np.exp(-0.5*(xx+np.exp(-xx)))
    
    return coeff*numrt

def nRootFunc(x,A,n):
    return A*(x**(1/n))

def paramListToVal(l):
    retVal = l
    exclude = False

    if type(l) == list:
        if l[1] == 'lh':
            exclude = True
        retVal = l[0]

    return exclude,retVal

def meansPerParams(i,indipParam,paramListOrHeader,meansDict,outDict,header=True):
    others = []
    
    if indipParam == 'h' or indipParam == 'l':
        indipParam += 'g'
    
    if header is False:
        _,pToAdd = paramListToVal(paramListOrHeader[indipParam][i][0])
    else:
        pToAdd = paramListOrHeader[indipParam]

    for k in paramListOrHeader.keys():
        if header is False:
            param = paramListOrHeader[k][i]
        else:
            param = [paramListOrHeader[k]]

        if k != indipParam and param is not None:
            exclude,othToAdd = paramListToVal(param[0])
            
            if exclude is False:
                others.append(othToAdd)

    others = tuple(others)

    if others in outDict:
        outDict[others].append((pToAdd,meansDict))
    else:
        outDict[others] = [(pToAdd,meansDict)]
    
    if 'nEvt' in meansDict.keys():
        outDict['nEvt'] = meansDict['nEvt']

def setupPlot(xlabel,ylabel,xlim,ylim,
              text=None,textXpos=0,textYpos=0,
              textHalign='left',textValign='top'):
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    
    ax = plt.gca()
    
    if xlim is not None:
        xmin = xlim[0]
        xmax = xlim[1]

        ticks = 10**floor(log10(xmax-xmin))

        ticksOK = ticks < xmax-xmin
        while ticksOK is False:
            ticks /= 10
            ticksOK = (True if ticks < xmax-xmin else False)

        plt.xticks(np.arange(xmin,xmax+ticks,ticks))
        plt.xlim(xmin,xmax)

        ax.xaxis.set_minor_locator(AutoMinorLocator(5))
        ax.xaxis.set_major_locator(AutoLocator())

    if ylim is not None:
        ymin = ylim[0]
        ymax = ylim[1]

        ticks = 10**floor(log10(ymax-ymin))

        ticksOK = ticks < ymax-ymin
        while ticksOK is False:
            ticks /= 10
            ticksOK = (True if ticks < ymax-ymin else False)
        
        plt.yticks(np.arange(ymin,ymax+ticks,ticks))
        plt.ylim(ymin,ymax)

        ax.yaxis.set_minor_locator(AutoMinorLocator(5))

    plt.minorticks_on()
    plt.grid(linestyle='-',which='both')

    if text is not None:
        # labels = [t for t in text.split('\n') if t != '']
        # handles = [mpl_patches.Rectangle((0, 0), 1, 1, fc="white", ec="white", 
        #                          lw=0, alpha=0)] * 2

        # plt.legend(handles, labels, 
        #            loc='best', fontsize='small', 
        #            fancybox=True, framealpha=0.7, 
        #            handlelength=0, handletextpad=0)
        plt.text(textXpos,textYpos,text,
                  bbox=dict(facecolor='white', alpha=1),
                  horizontalalignment=textHalign,
                  verticalalignment=textValign,
                  transform=ax.transAxes)

def setupFit(xFit,yFit,
             fitType='l',numDeg=0,minFit=None,maxFit=None,fitGuess=None,stddev=None):
    xMin = min(xFit) if minFit is None else minFit
    xMax = max(xFit) if maxFit is None else maxFit

    if stddev is not None:
        if type(stddev) == dict:
            xStdDev = stddev['x']
            yStdDev = stddev['y']
        else:
            xStdDev = None
            yStdDev = stddev

    try:

        if fitType == 'g':
            
            sigBins = []
            sigHist = []
            for i,h in enumerate(yFit):
                if xFit[i] > xMin and xFit[i] < xMax:
                    sigBins.append(xFit[i])
                    sigHist.append(h)
    
            xFitRes = [(sigBins[i+1]+sigBins[i])/2 for i in range(len(sigBins)-1)]
    
            if xFitRes == []:
                return None
    
            model = GaussianModel()

            if fitGuess != None:
                params = model.make_params(amplitude=fitGuess[0]*fitGuess[2]*np.sqrt(2*np.pi),
                                           center=fitGuess[1],
                                           sigma=fitGuess[2])
            else:
                params = model.guess(data=np.asarray(sigHist[:-1]),
                                     x=np.asarray(xFitRes))
            
            result = model.fit(np.asarray(sigHist[:-1]),
                               params=params,
                               weights=1.0/np.sqrt(np.asarray(sigHist[:-1])),
                               x=np.asarray(xFitRes),
                               nan_policy='omit')
            
            errs = np.sqrt(np.diag(result.covar))
            
            with open("fitReport.dat","a") as f:
                f.write(f"\nFit report curva {numDeg}\n")
                f.write(result.fit_report())
                f.write("\n")

        if fitType == 'n': ######## LOGNORMAL per i piedistalli
            sigBins = []
            sigHist = []
            for i,h in enumerate(yFit):
                if xFit[i] > xMin and xFit[i] < xMax:
                    sigBins.append(xFit[i])
                    sigHist.append(h)
    
            xFitRes = [(sigBins[i+1]+sigBins[i])/2 for i in range(len(sigBins)-1)]
    
            if xFitRes == []:
                return None
    
            model = LognormalModel()

            if fitGuess != None:
                params = model.make_params(amplitude=fitGuess[0]*fitGuess[2]*np.sqrt(2*np.pi),
                                           center=fitGuess[1],
                                           sigma=fitGuess[2])
            else:
                params = model.guess(data=np.asarray(sigHist[:-1]),
                                     x=np.asarray(xFitRes))
            
            result = model.fit(np.asarray(sigHist[:-1]),
                               params=params,
                               weights=1.0/np.sqrt(np.asarray(sigHist[:-1])),
                               x=np.asarray(xFitRes),
                               nan_policy='omit')
            
            errs = np.sqrt(np.diag(result.covar))
            
            with open("fitReport.dat","a") as f:
                f.write(f"\nFit report curva {numDeg}\n")
                f.write(result.fit_report())
                f.write("\n")

        if fitType == 'm':
            
            sigBins = []
            sigHist = []
            for i,h in enumerate(yFit):
                if xFit[i] > xMin and xFit[i] < xMax:
                    sigBins.append(xFit[i])
                    sigHist.append(h)
    
            xFitRes = [(sigBins[i+1]+sigBins[i])/2 for i in range(len(sigBins)-1)]
    
            if xFitRes == []:
                return None
    
            model = Model(moyalFunc)

            if fitGuess != None:
                params = model.make_params(A=fitGuess[0],
                                           mu=fitGuess[1],
                                           sigma=fitGuess[2])
            else:
                params = None
            
            result = model.fit(np.asarray(sigHist[:-1]),
                               params=params,
                               weights=np.sqrt(1.0/np.asarray(sigHist[:-1])),
                               x=np.asarray(xFitRes),
                               nan_policy='omit')
            
            errs = np.sqrt(np.diag(result.covar))
            
            with open("fitReport.dat","a") as f:
                f.write(f"\nFit report curva {numDeg} distribuzione di Moyal\n")
                f.write(result.fit_report())
                f.write("\n")

        if fitType == 'r':
            
            sigBins = []
            sigHist = []
            for i,h in enumerate(yFit):
                if xFit[i] > xMin and xFit[i] < xMax:
                    sigBins.append(xFit[i])
                    sigHist.append(h)
    
            xFitRes = [(sigBins[i+1]+sigBins[i])/2 for i in range(len(sigBins)-1)]
    
            if xFitRes == []:
                return None
    
            model = Model(nRootFunc)

            if fitGuess != None:
                params = model.make_params(A=fitGuess[0],
                                           n=fitGuess[1])
            else:
                params = None
            
            result = model.fit(np.asarray(sigHist[:-1]),
                               params=params,
                               weights=np.sqrt(1.0/np.asarray(sigHist[:-1])),
                               x=np.asarray(xFitRes),
                               nan_policy='omit')
            
            errs = np.sqrt(np.diag(result.covar))
            
            with open("fitReport.dat","a") as f:
                f.write(f"\nFit report curva {numDeg} distribuzione di Moyal\n")
                f.write(result.fit_report())
                f.write("\n")

        if fitType == 'p':
            model = PolynomialModel(degree=int(numDeg))
            
            params = model.make_params(c0=min(yFit),
                                       **{f"c{d}":1 for d in range(1,int(numDeg)+1)})

            xFitRes = []
            yFitRes = []
            weights = []
            for i,yy in enumerate(yFit):
                if xFit[i] > xMin and xFit[i] < xMax:
                    xFitRes.append(xFit[i])
                    yFitRes.append(yy)
                    if stddev is not None:
                        weights.append(1.0/yStdDev[i])
                    else:
                        weights.append(1)

            result = model.fit(np.asarray(yFitRes,dtype=float),
                               x=np.asarray(xFitRes,dtype=float),
                               weights=np.asarray(weights,dtype=float),
                               params=params,
                               nan_policy='omit')

            if result.covar is not None:
                errs = np.sqrt(np.diag(result.covar))
            else:
                errs = None
            
            with open("fitReport.dat","a") as f:
                f.write(f"\nFit report curva polinomiale di grado {numDeg}\n")
                f.write(result.fit_report())
                f.write("\n")

        if fitType == 's':
            xFitRes = []
            yFitRes = []
            weights = []
            for i,yy in enumerate(yFit):
                if xFit[i] > xMin and xFit[i] < xMax:
                    xFitRes.append(xFit[i])
                    yFitRes.append(yy)
                    if stddev is not None:
                        weights.append(1.0/yStdDev[i])
                    else:
                        weights.append(1)

            model = StepModel(form='logistic')
            
            params = model.guess(np.asarray(yFitRes,dtype=float),
                                 x=np.asarray(xFitRes,dtype=float))
            
            result = model.fit(np.asarray(yFitRes,dtype=float),
                               x=np.asarray(xFitRes,dtype=float),
                               weights=np.asarray(weights,dtype=float),
                               params=params,
                               nan_policy='omit')

            if result.covar is not None:
                errs = np.sqrt(np.diag(result.covar))

            else:
                errs = None
            
            with open("fitReport.dat","a") as f:
                f.write(f"\nFit report curva logistica\n")
                f.write(result.fit_report())
                f.write("\n")

    except OptimizeWarning:
        print("Impossibile trovare i parametri")
        return None
    except ValueError:
        print("Errore nei valori")
        return None

    return (xFitRes,
            result.best_fit,
            result.best_values,
            errs,
            result.chisqr,
            result.nfree,
            result.eval_uncertainty,
            result.eval,
            result.params)


def selectLim(pltType,nEvt,autoLim='',**kwargs):
    defaultLimits = {'e':{'x':(0,nEvt),
                          'y':(0,4095)},
                     'd':{'x':(0,4095),
                          'y':(0,nEvt)},
                     'b':{'x':(0,32),
                          'y':(0,4095)},
                     'c':{'v':{'x':(0,6),
                               'y':(0,4095)},
                          't':{'x':(0,150),
                               'y':(0,4095)},
                          'h':{'x':(0,600),
                               'y':(0,4095)},
                          'l':{'x':(0,60),
                               'y':(0,4095)},
                          's':{'x':(0,6),
                               'y':(0,4095)},
                          'q':{'x':(0,400),
                               'y':(0,4095)}}}

    cT = pltType[0]
    pT = pltType[-1]
    defLim = defaultLimits if cT != 'c' else defaultLimits['c']

    xlim = None
    ylim = None

    if f"{pT}x" not in autoLim:
        if f"{pT}xlim" in kwargs.keys():
            xlim = kwargs[f"{pT}xlim"]
        elif pT in defLim.keys():
            xlim = defLim[pT]['x']

    if f"{pT}y" not in autoLim:
        if f"{pT}ylim" in kwargs.keys():
            ylim = kwargs[f"{pT}ylim"]
        elif pT in defLim.keys():
            ylim = defLim[pT]['y']

    return xlim,ylim

def calibPlot(cit,gain,ch,indipVar,calibparams,xlabel,ylabel,xlim,ylim,
              fit=None,invAxes=False,qConv=False,msize=3,errorbars='sem',
              txtPos=None):
    initDir = os.getcwd()

    g = 'G' if (indipVar == 'h' or indipVar == 'l') else ''
    
    sh = 'shT' if indipVar == 's' else ''

    xTitleLbl,yTitleLbl = ((f"{indipVar.upper()}{sh}{g}","ADC") if invAxes is False 
                           else ("ADC",f"{indipVar.upper()}{sh}{g}"))

    chid = f"\n{cit.upper()} {gain.upper()} {ch.upper()}"

    xlabel,ylabel = (xlabel+chid,ylabel) if invAxes is False else (ylabel+chid,xlabel)

    if indipVar != 'q':
        meansPerX = calibparams[indipVar]
    else:
        meansPerX = calibparams['v']
    
    nEvents = 1
    if 'nEvt' in meansPerX.keys():
        nEvents = meansPerX['nEvt']

    if qConv:
        tWidth = f"{list(calibparams['v'].keys())[0][0]:.1f}"

    for k,v in meansPerX.items():
        if k != 'nEvt':
            vals = [f"{va}" for va in k]
            units = [f"{o}" for o in othersUnit[indipVar]]
    
            uStr = [f"{va}{un}" for va,un in zip(vals,units)]
            
            oDirStr = ''.join(uStr)
            atStr = ', '.join(uStr)
    
            othDir = f"per{indipVar.upper()}{sh}{g}{oDirStr}"
            if not os.path.exists(othDir):
                os.mkdir(othDir)
            os.chdir(othDir)

            x = [vv[0]*expIndip[indipVar] for vv in v]
            means = [vv[1] for vv in v]
            
            xm = list(zip(x,means))
            xm.sort()
            xm = np.asarray(xm)
            
            # if qConv:
                # print("Conversione in carica...")
                # qArr = qc.convToQ(tWidth,xm[:,0])
                # x = qArr[:,0]
                # xStdDev = qArr[:,1]
            # else:
                # x = xm[:,0]
                # xStdDev = None
            x = xm[:,0]
            xStdDev = None

            means = xm[:,1]
            
            adcMeans = np.asarray([m[cit][ch][gain]['mean'] for m in means],dtype=float)
            adcStdDev = np.asarray([m[cit][ch][gain]['stddev'] for m in means],dtype=float)

            xPoints,yPoints = (x,adcMeans) if invAxes is False else (adcMeans,x)

            stdDev = adcStdDev if xStdDev is None else {'x':xStdDev,'y':adcStdDev}

            fitRes = []
            if fit is not None:                    
                for p in fit:
                    fitRes.append((p,setupFit(xPoints,yPoints,*p[:-1],stddev=stdDev)))

            dTxt = ''
            if fitRes != []:
                for j,f in enumerate(fitRes):
                    xFitRes,bestFit,popt,perr,chi2,dof,uncert,func,params = f[1]

                    fitCurve = f[0][0]

                    numDeg = int(f[0][1])
                    
                    xFitMinP = f[0][2]
                    xFitMaxP = f[0][3]

                    xFitPlot = (np.linspace(xFitMinP,xFitMaxP,1000) if invAxes is False
                                else np.arange(xFitMinP,xFitMaxP,1))
                    yFitPlot = func(x=xFitPlot)#,**popt)
                    
                    uncertPlot = uncert(sigma=3,x=xFitPlot)
                    
                    color = f"{colors[j%len(colors)]}-"
                    
                    plt.plot(xFitPlot,yFitPlot,color,label=f"{j+1}")
                    # plt.fill_between(xFitPlot,yFitPlot-uncertPlot,yFitPlot+uncertPlot,
                    #                  color="#ABABAB")
    
                    if perr is not None:
                        poptKeys = [p for p in popt.keys() if p != 'form']
                        if fitCurve != 's':
                            poptNames = poptKeys
                        else:
                            poptNames = [logisParNames[p] for p in poptKeys]

                        dTxt += "\n".join([f"${poptNames[i]}_{j+1} = ({popt[pk]:.2e}) \pm ({perr[i]:.2e})$" 
                                           for i,pk in enumerate(poptKeys)])
                    else:
                        dTxt += "\n".join([f"$c{i}_{j+1} = {po:.2e}$" 
                                           for i,po in enumerate(popt.values())])

                    dTxt += f"\n$\chi^2_{j+1}/dof = {chi2:.2f}/{dof}$\n"
                    
                    xlabel += f"\n${yTitleLbl} = "
                    if fitCurve != 's':
                        xlabel += f'+'.join([f"c{i}_{j+1} \cdot {xTitleLbl}{int(i > 1)*f'^{i}'}" 
                                             for i in range(numDeg,0,-1)])
                        xlabel += f"+c0_{j+1}$"
                    else:
                        xlabel += f"A\cdot (1-(1+e^{{\\frac{{V - \mu}}{{\sigma}}}})^{{-1}})$"

                    
                    with open(f"fitFunc{j+1}-{cit}-{gain}-{ch}-{othDir}.dat","w") as fitPointsOut:
                        fitPointsOut.write("x,y,yerr\n\n")
                        for i,xx in enumerate(xFitPlot):
                            fitPointsOut.write(f"{xx},{yFitPlot[i]},{uncertPlot[i]}\n")

            if txtPos is None:
                txtPos = (0.5,0.5)

            setupPlot(xlabel,ylabel,xlim[f"c{indipVar}"],ylim[f"c{indipVar}"],
                      text=dTxt,textXpos=txtPos[0],textYpos=txtPos[1],
                      textHalign='left',textValign='top')

            plt.title(f"{yTitleLbl} vs {xTitleLbl} @ {atStr}")

            plt.plot(xPoints,yPoints,'r.',markersize=msize)

            plt.legend(loc='lower right')

            if errorbars == 'sem':
                stdErr = adcStdDev/np.sqrt(nEvents)
            elif errorbars == 'stddev':
                stdErr = adcStdDev
            else:
                stdErr = None

            xerr,yerr = (None,stdErr) if invAxes is False else (stdErr,None)

            plt.errorbar(xPoints,yPoints,xerr=xerr,yerr=yerr,fmt='none')
            plt.savefig(f"plot-{cit}-{gain}-{ch}-{othDir}.png",
                        dpi=300,bbox_inches='tight')
            plt.clf()
            
            with open(f"data-{cit}-{gain}-{ch}-{othDir}.dat","w") as outFile:
                outFile.write(f"{indipVar},adc,stdAdc\n")
                for i,xx in enumerate(x):
                    outFile.write(f"{xx},{adcMeans[i]},{adcStdDev[i]}\n")
            
            os.chdir(initDir)

def plotData(name,citDict,meansDict,plotType,cits,gains,channels,**kwargs):
    cits = csl.argToList(cits,["cit0","cit1"])
    gains = csl.argToList(gains,["hg","lg"])
    channels = csl.argToList(channels,list(csl.chToNum.keys()))

    xlim = {}
    ylim = {}
    
    nEvt = 0
    if citDict is not None:
        nEvt = citDict['nEvt']

    if 'directory' in kwargs.keys():
        os.chdir(kwargs['directory'])

    if 'markersize' in kwargs.keys():
        msize = kwargs['markersize']
    else:
        msize = 3
    
    if 'errorbars' in kwargs.keys():
        errbars = kwargs['errorbars']
    else:
        errbars = 'sem'
    
    if 'txtpos' in kwargs.keys():
        txtPos = kwargs['txtpos']
    else:
        txtPos = (0.95,0.95)

    for p in plotType:
        autoLimStr = ('calib'*int(p == 'c'))+'autolim'

        autoLim = ''
        if autoLimStr in kwargs.keys():
            autoLim = kwargs[autoLimStr]

        if (p == 'c') and ('indipVar' in kwargs.keys()):
            p += kwargs['indipVar']

        xlim[p],ylim[p] = selectLim(p,nEvt,autoLim,**kwargs)

    dataDir = os.getcwd()
    for c in cits:
        if not os.path.exists(c):
            os.mkdir(c)
        os.chdir(c)

        citDir = os.getcwd()
        for g in gains:
            if not os.path.exists(g):
                os.mkdir(g)
            os.chdir(g)

            if 'e' in plotType:
                evts = list(range(nEvt))
                
                for ch in channels:
                    chid = f"{c.upper()} {g.upper()} {ch.upper()}"
                    setupPlot(f"Evento\n{chid}","ADC",xlim['e'],ylim['e'])
                    plt.ticklabel_format(style='sci', axis='x', scilimits=(0,3))

                    plt.plot(evts,
                             citDict[c][ch][g],
                             'b.')
                    plt.savefig(f"{name}-{c}-{ch}-{g}.png",
                                dpi=300,bbox_inches='tight')
                    plt.clf()
            
            if 'b' in plotType:
                chid = f"{c.upper()} {g.upper()}"
                setupPlot(f"Canale\n{chid}","<ADC>",xlim['b'],ylim['b'])
                plt.minorticks_off()
                channelsStr = [f"CH{j}" for j in range(32)]
                plt.xticks(np.arange(0,32),channelsStr,rotation=90)

                plt.bar(channelsStr,[meansDict[c][f"ch{chn:02d}"][g]['mean'] for chn in range(32)],
                        yerr=[meansDict[c][f"ch{chn:02d}"][g]['stddev']/np.sqrt(nEvt) for chn in range(32)])
                plt.savefig(f"allch-{name}-{c}-{g}.png",
                            dpi=300,bbox_inches='tight')
                plt.clf()
            
            if 'd' in plotType:
                for ch in channels:
                    chid = f"{c.upper()} {g.upper()} {ch.upper()}"
                    
                    dTxt = f"Entries {nEvt}"

                    binsWidth = None
                    if 'bins' in kwargs.keys():
                        binsWidth = np.arange(min(citDict[c][ch][g]),
                                              max(citDict[c][ch][g])+kwargs['bins'],
                                              kwargs['bins'])

                    n,binEdges,patches = plt.hist(citDict[c][ch][g],
                                                  bins=binsWidth,
                                                  color='red')

                    fitRes = []                    
                    if 'fit' in kwargs.keys():
                        for p in kwargs['fit']:
                            
                            fitType = p[0]
                        
                            setupFitRes = setupFit(binEdges,n,*p)
                            nPlot = int(p[1])
                            confBands = True if p[-1] != 'n' else False

                            if setupFitRes is not None:
                                fitRes.append((p[0],nPlot,setupFitRes,confBands))
                                xFitRes,bestFit,popt,perr,chi2,dof,uncert,func,params = setupFitRes
                                
                                ampl,amplErr = (params['height'].value,
                                                params['height'].stderr)
                                
                                centr,centrErr = (params['center'].value,
                                                  params['center'].stderr)
                                
                                sigma,sigmaErr = (params['sigma'].value,
                                                  params['sigma'].stderr)
                                
                                
                                if fitType == 'n':
                                    mu,muErr = centr,centrErr
                                    s,sErr = sigma,sigmaErr

                                    centr = np.exp(mu-s**2)
                                    centrErr = centr*np.sqrt((muErr)**2+(4*s**2*sErr**2)**2)
                                    
                                    sigma = np.sqrt((np.exp(s**2)-1)*np.exp(2*mu+s**2))
                                    sigmaErr = sigma*np.sqrt(
                                        (muErr)**2+
                                        ((((2*np.exp(s**2))-1)/(np.exp(s**2)-1))**2*s**2*sErr**2))
                                
                                dTxt += (f"\n$A_{{{nPlot}}} = {ampl:.2f} \pm {amplErr:.2f}$\n"
                                         f"$\mu_{{{nPlot}}} = {centr:.2f} \pm {centrErr:.2f}$\n"
                                         f"$\sigma_{{{nPlot}}} = {sigma:.2f} \pm {sigmaErr:.2f}$\n"
                                         f"$\chi_{{{nPlot}}}^2/dof = {chi2:.2f}/{dof}$")
                            else:
                                print(f"Fit non possibile per la curva {nPlot}")
                    
                    setupPlot(f"ADC\n{chid}","N",xlim['d'],ylim['d'],
                              text=dTxt,textXpos=txtPos[0],textYpos=txtPos[1])

                    if fitRes != []:
                        for f in fitRes:
                            fitFunc = f[2][-2]
                            xp = np.linspace(min(f[2][0]),
                                             max(f[2][0]),
                                             num=1000)#f[2][0]
                            yp = fitFunc(x=xp)#f[2][1]
                            
                            xu = f[2][0]
                            yu = f[2][1]
                            
                            label = f[1]
                            uncert = f[2][6]
                            confBands = f[3]
                            plt.plot(xp,yp,label=label)
                            
                            uncertPlot = uncert(sigma=3)
                            
                            if confBands is True:
                                plt.fill_between(xu,
                                                 yu-uncertPlot,
                                                 yu+uncertPlot,
                                                 color="#ABABAB",
                                                 zorder=0)
                        
                        plt.legend(loc='lower right')

                    plt.savefig(f"hist-{name}-{c}-{ch}-{g}.png",
                                dpi=300,bbox_inches='tight')
                    plt.clf()
            
            if 'c' in plotType:
                paramsOK = False
                calibPOK = 'calibparams' in kwargs.keys()

                fitParams = None
                if 'fit' in kwargs.keys():
                    fitParams = kwargs['fit']

                if calibPOK:
                    paramsOK = (('v' in kwargs['calibparams'].keys() or
                                 't' in kwargs['calibparams'].keys() or
                                 'h' in kwargs['calibparams'].keys() or
                                 'l' in kwargs['calibparams'].keys() or
                                 's' in kwargs['calibparams'].keys()) and
                                ('indipVar' in kwargs.keys() and
                                 'invAxes' in kwargs.keys()))

                if paramsOK is True:
                    for ch in channels:
                        if 'v' in kwargs['indipVar']:
                            calibPlot(c,g,ch,'v',kwargs['calibparams'],
                                      "V (V)","<ADC>",xlim,ylim,fitParams,
                                      invAxes=kwargs['invAxes'],
                                      msize=msize,errorbars=errbars,
                                      txtPos=txtPos)
                        if 't' in kwargs['indipVar']:
                            calibPlot(c,g,ch,'t',kwargs['calibparams'],
                                      "T (ns)","<ADC>",xlim,ylim,fitParams,
                                      invAxes=kwargs['invAxes'],
                                      msize=msize,errorbars=errbars,
                                      txtPos=txtPos)
                        if 'h' in kwargs['indipVar']:
                            calibPlot(c,g,ch,'h',kwargs['calibparams'],
                                      "HG","<ADC>",xlim,ylim,fitParams,
                                      invAxes=kwargs['invAxes'],
                                      msize=msize,errorbars=errbars,
                                      txtPos=txtPos)
                        if 'l' in kwargs['indipVar']:
                            calibPlot(c,g,ch,'l',kwargs['calibparams'],
                                      "LG","<ADC>",xlim,ylim,fitParams,
                                      invAxes=kwargs['invAxes'],
                                      msize=msize,errorbars=errbars,
                                      txtPos=txtPos)
                        if 's' in kwargs['indipVar']:
                            calibPlot(c,g,ch,'s',kwargs['calibparams'],
                                      "Tconst","<ADC>",xlim,ylim,fitParams,
                                      invAxes=kwargs['invAxes'],
                                      msize=msize,errorbars=errbars,
                                      txtPos=txtPos)
                        if 'q' in kwargs['indipVar']:
                            calibPlot(c,g,ch,'q',kwargs['calibparams'],
                                      "Q (pC)","<ADC>",xlim,ylim,fitParams,
                                      invAxes=kwargs['invAxes'],qConv=True,
                                      msize=msize,errorbars=errbars,
                                      txtPos=txtPos)

            os.chdir(citDir)

        os.chdir(dataDir)
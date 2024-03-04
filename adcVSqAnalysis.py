# -*- coding: utf-8 -*-
"""
Created on Thu Dec 21 16:28:27 2023

@author: limadou
"""

import numpy as np
import matplotlib.pyplot as plt
from lmfit.models import LinearModel

impDataFile = {"5ns"  : "D:/TB_FM/triggerBoardLibs/impCalib5ns.dat",
               "10ns" : "D:/TB_FM/triggerBoardLibs/impCalib10ns.dat",
               "50ns" : "D:/TB_FM/triggerBoardLibs/impCalib50ns.dat"}

adcDataFile = {"5ns"  : {'hg' : "D:/TB_FM/triggerBoardLibs/fineCalib20HG2LG50tShap_ch00/analisiHG_nofit/calibCurves/cit0/hg/perV5.0ns20.0hg2.0lg/data-cit0-hg-ch00-perV5.0ns20.0hg2.0lg.dat",
                         'lg' : "D:/TB_FM/triggerBoardLibs/fineCalib20HG2LG50tShap_ch00/analisiLG_nofit/calibCurves/cit0/lg/perV5.0ns20.0hg2.0lg/data-cit0-lg-ch00-perV5.0ns20.0hg2.0lg.dat"},
               "10ns" : {'hg' : "D:/TB_FM/triggerBoardLibs/fineCalib20HG2LG50tShap_ch05/analisiHG_nofit/calibCurves/cit0/hg/perV10.0ns20.0hg2.0lg/data-cit0-hg-ch05-perV10.0ns20.0hg2.0lg.dat",
                         'lg' : "D:/TB_FM/triggerBoardLibs/fineCalib20HG2LG50tShap_ch05/analisiLG_nofit/calibCurves/cit0/lg/perV10.0ns20.0hg2.0lg/data-cit0-lg-ch05-perV10.0ns20.0hg2.0lg.dat"},
               "50ns" : {'hg' : "D:/TB_FM/triggerBoardLibs/calibFM50ns/calibHG/calibCurves/cit0/hg/perV50.0ns10.0hg1.5lg/data-cit0-hg-ch09-perV50.0ns10.0hg1.5lg.dat",
                         'lg' : "D:/TB_FM/triggerBoardLibs/calibFM50ns/calibLG/calibCurves/cit0/lg/perV50.0ns10.0hg1.5lg/data-cit0-lg-ch09-perV50.0ns10.0hg1.5lg.dat"}}

tToCH = {"5ns"  : "CH00",
         "10ns" : "CH05",
         "50ns" : "CH09"}

limits = {"5ns"  : {'hg' : (0,1.2e-10),
                    'lg' : (0,5.4e-10)},
          "10ns" : {'hg' : (0,0.3e-9),
                    'lg' : (0,1.1e-9)},
          "50ns" : {'hg' : (0, 1e-9),
                    'lg' : (0, 6e-9)}}

steps = {'hg':3,
         'lg':12}

fitLim = {"5ns"  : {'hg' : (0.2e-10, 0.8e-10),
                    'lg' : (1.00e-10, 3.00e-10)},
          "10ns" : {'hg' : (0.70e-10, 1.80e-10),
                    'lg' : (0.40e-09, 1.1e-09)},
          "50ns" : {'hg' : (0, 0.9e-9),
                    'lg' : (0, 5.5e-9)}}

impData = {k : np.genfromtxt(v,delimiter=',',names=True)
           for k,v in  impDataFile.items()}

adcData = {k : {kg : np.genfromtxt(vg,delimiter=',',names=True)
                for kg,vg in v.items()}
           for k,v in adcDataFile.items()}

gainVal = {"5ns":{'hg':20,'lg':2},
           "10ns":{'hg':20,'lg':2},
           "50ns":{'hg':10,'lg':1.5}}

for t in ("5ns","10ns","50ns"):
    for g in ('hg','lg'):
        for f in ('Fit','NoFit'):
            G = g.upper()
            gval = gainVal[t][g]
            ch = tToCH[t]
    
            plt.title(f"ADC vs Q @ CIT0 {ch} {G}={gval}")
            plt.xlabel("Q (C)\n$ADC = a \cdot Q + b$")
            plt.ylabel("<ADC>")
            plt.grid(which='both')
            plt.minorticks_on()
            plt.xlim(limits[t][g])
            
            if t != "50ns":
                ms = 1
                x = impData[t]['charge'][::steps[g]]
                xerr = impData[t]['Scharge'][::steps[g]]
                y = adcData[t][g]['adc'][::steps[g]]
                yerr = adcData[t][g]['stdAdc'][::steps[g]]
            else:
                ms = 4
                vToQ50ns = {k:(q,qerr) for k,q,qerr in zip(impData['50ns']['Vimp'],impData['50ns']['charge'],impData['50ns']['Scharge'])}
                
                x = np.asarray([vToQ50ns[round(v,6)][0] for v in adcData[t][g]['v']])
                xerr = [vToQ50ns[round(v,6)][1] for v in adcData[t][g]['v']]
                y = adcData[t][g]['adc']
                yerr = adcData[t][g]['stdAdc']

            plt.errorbar(x, y,
                         xerr=xerr, yerr=yerr,
                         fmt='none',elinewidth=0.7)

            plt.plot(x, y, 'r.',markersize=ms)

            if f == 'Fit':
                ax = plt.gca()

                xmin = np.where(x > fitLim[t][g][0])[0][0]
                xmax = np.where(x < fitLim[t][g][1])[0][-1]
                
                model = LinearModel()
                
                q = np.asarray(x[xmin:xmax])
                adc = np.asarray(y[xmin:xmax])
                w = 1/np.sqrt(np.asarray(y[xmin:xmax]))
                
                params = model.guess(adc, x=q)
                
                result = model.fit(adc, x=q, weights=w, params=params)

                plt.plot(q,result.eval(x=q),'g-',linewidth=1)
                
                plt.text(0.5,0.2,
                          (f"$a = ({result.params['slope'].value:.2e}) \pm "
                            f"({result.params['slope'].stderr:.2e})$\n"
                            f"$b = ({result.params['intercept'].value:.2e}) \pm "
                            f"({result.params['intercept'].stderr:.2e})$\n"
                            f"$\chi^2/dof = {result.chisqr:.0f}/"
                            f"{result.nfree}$"),
                          bbox=dict(facecolor='white', alpha=1),
                          horizontalalignment='left',
                          verticalalignment='top',
                          transform=ax.transAxes)
    
            plt.savefig(f"{ch}{G}{gval}calib{f}{t}.png",
                        dpi=600,bbox_inches='tight')
    
            plt.clf()
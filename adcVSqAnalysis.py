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
                         'lg' : "D:/TB_FM/triggerBoardLibs/fineCalib20HG2LG50tShap_ch05/analisiLG_nofit/calibCurves/cit0/lg/perV10.0ns20.0hg2.0lg/data-cit0-lg-ch05-perV10.0ns20.0hg2.0lg.dat"}}

tToCH = {"5ns"  : "CH00",
         "10ns" : "CH05"}

limits = {"5ns"  : {'hg' : (0,1.2e-10),
                    'lg' : (0,5.4e-10)},
          "10ns" : {'hg' : (0,0.3e-9),
                    'lg' : (0,1.1e-9)}}

steps = {'hg':3,
         'lg':12}

fitLim = {"5ns"  : {'hg' : (0.2e-10, 0.8e-10),
                    'lg' : (1.00e-10, 3.00e-10)},
          "10ns" : {'hg' : (0.70e-10, 1.80e-10),
                    'lg' : (0.40e-09, 1.1e-09)}}

impData = {k : np.genfromtxt(v,delimiter=',',names=True)
           for k,v in  impDataFile.items()}

adcData = {k : {kg : np.genfromtxt(vg,delimiter=',',names=True)
                for kg,vg in v.items()}
           for k,v in adcDataFile.items()}

for t in ("5ns","10ns"):
    for g in ('hg','lg'):
        for f in ('Fit','NoFit'):
            G = g.upper()
            gval = 20 if g=='hg' else 2
            ch = tToCH[t]
    
            plt.title(f"ADC vs Q @ CIT0 {ch} {G}={gval}")
            plt.xlabel("Q (C)\n$ADC = a \cdot Q + b$")
            plt.ylabel("<ADC>")
            plt.grid(which='both')
            plt.minorticks_on()
            plt.xlim(limits[t][g])

            plt.errorbar(impData[t]['charge'][::steps[g]],
                         adcData[t][g]['adc'][::steps[g]],
                         xerr=impData[t]['Scharge'][::steps[g]],
                         yerr=adcData[t][g]['stdAdc'][::steps[g]],
                         fmt='none',elinewidth=0.7)

            plt.plot(impData[t]['charge'][::steps[g]],
                     adcData[t][g]['adc'][::steps[g]],
                     'r.',markersize=1)

            if f == 'Fit':
                ax = plt.gca()

                xmin = np.where(np.asarray(impData[t]['charge'])
                                > fitLim[t][g][0])[0][0]
                xmax = np.where(np.asarray(impData[t]['charge'])
                                < fitLim[t][g][1])[0][-1]
                
                model = LinearModel()
                
                q = np.asarray(impData[t]['charge'][xmin:xmax:steps[g]])
                adc = np.asarray(adcData[t][g]['adc'][xmin:xmax:steps[g]])
                w = 1/np.sqrt(np.asarray(adcData[t][g]['adc'][xmin:xmax:steps[g]]))
                
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
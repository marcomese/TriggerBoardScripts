# -*- coding: utf-8 -*-
import numpy as np
from lmfit.models import LinearModel

carattData = {'10.0' : np.genfromtxt("D:/TB2/triggerBoardLibs/carattIngrTB2_10ns.dat",delimiter=',',names=True),
              '40.0' : np.genfromtxt("D:/TB2/triggerBoardLibs/carattIngrTB2_40ns.dat",delimiter=',',names=True)}

VimpToQ = {tk:{k:v for k,v in zip(carattData[tk]['Vimp'],carattData[tk]['area'])} 
           for tk in carattData.keys()}

SVimpToQ = {tk:{k:v for k,v in zip(carattData[tk]['Vimp'],carattData[tk]['Sarea'])} 
           for tk in carattData.keys()}

model = LinearModel()

result = {tk:model.fit(np.asarray(carattData[tk]['area']),
                       weights=np.sqrt(1.0/np.asarray(carattData[tk]['Sarea'])),
                       x=np.asarray(carattData[tk]['Vimp']),
                       nan_policy='omit') for tk in carattData.keys()}

def convToQ(tWidth,vimpArr,scale=1e-12):
    qOut = np.zeros((len(vimpArr),2))

    sc = 1/scale

    for i,v in enumerate(vimpArr):
        if v in VimpToQ[tWidth].keys():
            qOut[i,:] = (VimpToQ[tWidth][v]*sc,SVimpToQ[tWidth][v]*sc)
        else:
            qOut[i,:] = (result[tWidth].eval(x=v)*sc,
                         result[tWidth].eval_uncertainty(sigma=3,x=v)[0]*sc)
    
    return qOut
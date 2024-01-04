# -*- coding: utf-8 -*-
"""
Created on Thu Dec 16 16:15:02 2021

@author: limadou
"""

import numpy as np
from itertools import product
from collections import defaultdict

validQ = defaultdict(list)

q = [2e-12,5e-12,10e-12,50e-12,100e-12,400e-12,1000e-12,4800e-12]

validQ = {qq:[] for qq in q}

v = [15,20,30,40,50,60,70,80,90,100,150,200,250,300,350,400,450,500,550,600,
     650,700,750,800,850,900,950,1000,1500,2000,2500,3000,3500,4000,4500,5000,
     5500,6000]

t = [5,10,15,20,25,30,35,40,45,50]

allQ = [(vv,tt,float(f"{(vv*tt/50)*1e-12:.1e}")) for tt,vv in product(t,v)]

# sqQ = [(vv,tt,float(f"{(vv*tt/50)*1e-12:.0e}")) for vv,tt in zip(v,t)]

for aq in allQ:
    if aq[2] in validQ.keys():
        validQ[aq[2]].append((aq[0],aq[1]))
# validQ = [qq for qq in allQ if qq[2] in q]
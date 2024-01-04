# -*- coding: utf-8 -*-
"""
Created on Wed Mar 22 17:36:24 2023

@author: mames
"""

import triggerBoardLib as tbl
import alimLib as alim
from time import sleep

alimAddr = 'USB0::0x0957::0x0F07::MY53004295::0::INSTR'
oscAddr = 'TCPIP0::jemeusohd06k.na.infn.it::inst0::INSTR'
impAddr = 'TCPIP0::jemeusot3awg3k.na.infn.it::inst0::INSTR'
dpcuEmulatorAddr = '172.16.1.2'

f = open("testREFDAC_cit0_cit1.txt","a")

for i in range(100):
    tbAlim = alim.triggerBoardAlim(alimAddr)
    
    tbAlim.powerOnChannel(2)
    
    tb = tbl.triggerBoard(alimAddr,dpcuEmulatorAddr)
    
    tb.syncTBRegisters()
    
    tb.powerOnCIT("cit0")
    
    tb.powerOnCIT("cit1")
    
    sleep(1)

    status = tb.readRegister("STATUS_REG")

    print(status)
    
    f.write(f"{status}\n")

    tb.powerOff(2)
    
    sleep(1)
    
f.close()
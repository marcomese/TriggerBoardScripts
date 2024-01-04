# -*- coding: utf-8 -*-
"""
Created on Tue Nov 10 15:38:09 2020

@author: Marco
"""

import pyvisa as pv
from time import sleep
import re

class triggerBoardAlim(object):
    def __init__(self,alimAddr):
        self._resName = alimAddr
        
        self._rm = pv.ResourceManager()
        
        self._device = self._rm.open_resource(self._resName)

        self._device.write("SOUR:VOLT:LEVel 12,(@1,2);:CURR:LEV 1,(@1,2)")
        
        self.sideToCH = {"hot"  : 1, "cold" : 2}
        self.chToSide = {v:k for k,v in self.sideToCH.items()}

        self.sideStatus = {self.chToSide[c+1]:stat 
                           for c,stat in enumerate(self.getActiveChannels())}

        self.currentMonitoring = False
        self.monitorCurrentProc = None

    def getActiveChannels(self):
        activeChPattern = "(\d),(\d)\\n"
        activeChReg = re.compile(activeChPattern) 
        
        activeChStr = self._device.query("OUTP:STAT? (@1,2)")
        
        activeChMatch = activeChReg.match(activeChStr)
        
        return [int(ac) for ac in activeChMatch.groups()]

    def powerOnSide(self, side, sleepTime=1):
        if side.lower() not in ("hot", "cold"):
            raise Exception(f"ERRORE: Lato {side} non impostabile\n"
                            "E' possibile scegliere solo lato 'hot' o 'cold'")

        print("Spengo prima tutte le uscite dell'alimentatore...")
        self._device.write("OUTP:STAT OFF,(@1,2)")
        self.sideStatus = {"hot" : 0, "cold" : 0}

        print(f"Attendo {sleepTime} secondi prima di accendere il lato {side}...")
        sleep(sleepTime)

        print(f"Accendo il lato {side}")
        ch = self.sideToCH[side]
        self._device.write(f"OUTP:STAT ON,(@{ch})")
        self.sideStatus[side.lower()] = 1

    def powerOffSide(self, side):
        if side.lower() not in ("hot", "cold"):
            raise Exception(f"ERRORE: Lato {side} non impostabile\n"
                            "E' possibile scegliere solo lato 'hot' o 'cold'")

        print(f"Spengo il lato {side}...")
        ch = self.sideToCH[side.lower()]
        self._device.write(f"OUTP:STAT OFF,(@{ch})")

        self.sideStatus[side.lower()] = 0

    def powerOnChannel(self, ch, sleepTime=1):
        print(f"Attendo {sleepTime} secondi prima di accendere il canale {ch}...")
        sleep(sleepTime)

        print(f"Accendo il canale {ch}")
        self._device.write(f"OUTP:STAT ON,(@{ch})")
        
        self.sideStatus[self.chToSide[ch]] = 1

    def powerOffChannel(self, ch):
        print(f"Spengo il canale {ch}...")
        self._device.write(f"OUTP:STAT OFF,(@{ch})")
        
        self.sideStatus[self.chToSide[ch]] = 0

    def getCurr(self):
        if len(self.sideStatus) == 0:
            return "Nessun canale attivo!"
        else:
            ass = []

            channelStr = "(@"

            hotStat = self.sideStatus['hot']
            coldStat = self.sideStatus['cold']
            
            if hotStat == 0 and coldStat == 1:
                channelStr += "2)"
            elif hotStat == 1 and coldStat == 1:
                channelStr += "1,2)"
            else:
                channelStr += "1)"
            
            ass.append(self._device.query(f"MEAS:CURR? {channelStr}"))

            return ass

    def dataLogStart(self,intFileName,time=90,channel=1):
        self._device.write(f"SENSE:DLOG:CURRENT:RANGE:AUTO ON, (@{channel})")
        self._device.write(f"SENSE:DLOG:VOLTAGE:RANGE:AUTO ON, (@{channel})")
        self._device.write(f"SENSE:DLOG:FUNCTION:VOLTAGE OFF, (@{channel})")
        self._device.write(f"SENSE:DLOG:FUNCTION:CURRENT ON, (@{channel})")
        self._device.write(f"SENSE:DLOG:PERIOD 0.000100")
        self._device.write(f"SENSE:DLOG:TIME {time}")

        self._device.write(f'INITIATE:IMMEDIATE:DLOG "Internal:\\{intFileName}.dlog"')

    def exportLoggedData(self,intFileName):
        self._device.write(f'MMEMORY:EXPORT:DLOG "Internal:\{intFileName}.csv"')

    def getLoggedData(self,intFileName):
        print("Inizio il download dei dati...")
        data = self._device.query(f'MMEM:DATA? "Internal:\{intFileName}.csv"')

        print("Dati scaricati, scrivo sul file...")
        with open(f"{intFileName}_pwrLog.csv","w") as f:
            f.write(data)

        print(f"File {intFileName}_pwrLog.csv generato")

    def getLoggerStatus(self):
        self._device.write(f"SENSE:DLOG:PERIOD MIN")
        
    def close(self):
        self._device.close()
        self._rm.close()


#alim = triggerBoardAlim()
#
#selOk = False
#
#while selOk == False:
#    side = input("Scegliere il lato della Trigger Board (hot/cold): ")
#    if side.lower() == "hot" or side.lower() == "cold":
#        selOk = True
#    else:
#        selOk = False
#
#alim.powerOnSide(side)
#print(alim.getCurrAss())
#
#alim.close()

#from multiprocessing import Process
#    def _currMon(self):
#        ass = self.getCurr()
#        for i,c in enumerate(ass):
#            print(f"Corrente lato {self.chToSide[i+1]}: {c}")
#
#    def monitorCurrent(self):
#        self.monitorCurrentProc = Process(target = self._currMon, args = (self))
#        self.monitorCurrentProc.start()
#        self.currentMonitoring = True
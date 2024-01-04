# -*- coding: utf-8 -*-
"""
Created on Thu Nov 24 18:06:41 2022

@author: limadou
"""

import triggerBoardLib as tblib
import alimLib as alm
from time import sleep
import pulseGenLib as pgen

channel = 'ch31'

impFrequency = 20

pulseAmpl = 400e-3
pulseWidth = 10e-9

trgMask = "04000000"
genericMask = None#"00000004"

evtNum = 600

feedback = True

dpcuRun = True

getPedestals = False

# dacPedestalCIT0 = "32643246"
# dacPedestalCIT1 = "31003196"

dacPedestalCIT0 = "317E31C6" # pedestals for SN05
dacPedestalCIT1 = "31003100"

threshold = 220

shapingTime = 50

alimAddr = 'USB0::0x0957::0x0F07::MY53004295::0::INSTR'
impAddr = 'TCPIP0::jemeusot3awg3k.na.infn.it::inst0::INSTR'
dpcuEmulatorAddr = '172.16.1.2'

tbAlim = alm.triggerBoardAlim(alimAddr)

tbAlim.powerOnChannel(2)
sleep(2)
print("Scheda trigger accesa!")

impSer = pgen.pulseGenerator(impAddr)
impSer.configurePulse(1,pulseAmpl,0,
                      pulseWidth,2e-9,2e-9,impFrequency)

impSer.configurePulse(2,3.3,0,
                      30e-9,2e-9,2e-9,impFrequency,
                      double=False,vocm=0.5)

impSer.coupleToChannel1("frequency")
impSer.coupleToChannel1("phase")

print("Impulsatore configurato!")

tb = tblib.triggerBoard(alimAddr, dpcuEmulatorAddr)

print("Sincronizzazione registri Trigger Board")
tb.syncTBRegisters()
print("Sincronizzazione completata")

tb.powerOnCIT("cit0")
sleep(1)
print("Citiroc 0 acceso!")
tb.powerOnCIT("cit1")
sleep(1)
print("Citiroc 1 acceso!")

tb.tConstShaper = {'hg':shapingTime,'lg':shapingTime}



print(f"Shaping time impostato a {shapingTime}")

tb.thresholds = {'charge' : threshold,
                 'time'   : threshold}

print(f"Soglie impostate a {threshold}")

tb.gains = {
    channel : {'hg': 5.0, 'lg': 5.0, 'inCalib': 'hg', 'enabled': True},
}

tb.configure("all")
sleep(1)
print("Citiroc configurati!")

tb.slowCtrl.selectPrescaler(0,1,feedback=feedback)
print("Prescaler M0 impostato!")

tb.slowCtrl.selectPrescaler(1,1,feedback=feedback)
print("Prescaler M1 impostato!")

tb.slowCtrl.selectPrescaler(2,1,feedback=feedback)
print("Prescaler M2 impostato!")

tb.slowCtrl.selectPrescaler(3,1,feedback=feedback)
print("Prescaler M3 impostato!")

tb.triggerMask = trgMask
sleep(1)
print(f"Maschera di trigger {trgMask} selezionata!")

if genericMask is not None:
    tb.genericTriggerMask = genericMask
    print(f"Maschera di trigger generica {genericMask} selezionata!")

print("Maschera di trigger applicata!")

tb.pedestals = {'cit0': {'hg': dacPedestalCIT0[:4],
                         'lg': dacPedestalCIT0[4:]},
                'cit1': {'hg': dacPedestalCIT1[:4],
                         'lg': dacPedestalCIT1[4:]}}

print("Piedistalli configurati")

fileName = f"testAllChSN05_{channel}"

tb.slowCtrl.flushRegisters(feedback=feedback)
tb.startAcq()
print("Acquisizione avviata!")

tb.slowCtrl.startDPCURun()

impSer.turnOnChannel("all")
impSer.startPulseGenerator()
print("Impulsatore avviato!")

tb.saveData(evtNum, fileName)

tb.slowCtrl.stopDPCURun()

tb.slowCtrl.stopACQ(feedback=feedback)
print("Acquisizione arrestata!")

sleep(1)

impSer.turnOffChannel("ch1")
impSer.turnOffChannel("ch2")
impSer.stopPulseGenerator()

tb.slowCtrl.powerOffCIT("all")
sleep(1)
print("Citiroc spenti!")

tbAlim.powerOffChannel(2)
print("Scheda spenta!")

tb.close()

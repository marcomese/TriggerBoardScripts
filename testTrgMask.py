# -*- coding: utf-8 -*-
"""
Created on Tue Sep  6 17:20:37 2022

@author: limadou
"""

import triggerBoardLib as tblib
import alimLib as alm
from time import sleep, perf_counter

trgMask = "04000000"
genericMask = None#"00000004"

evtNum = 600

feedback = True

dpcuRun = True

getPedestals = False

dacPedestalCIT0 = "32643246"
dacPedestalCIT1 = "31003196"

threshold = 220

shapingTime = 50

alimAddr = 'USB0::0x0957::0x0F07::MY53004295::0::INSTR'
dpcuEmulatorAddr = '172.16.14.52'

tbAlim = alm.triggerBoardAlim(alimAddr)

tbAlim.powerOnChannel(2)
sleep(2)
print("Scheda trigger accesa!")

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
    'ch31': {'hg': 5.0, 'lg': 5.0, 'inCalib': 'hg', 'enabled': True},
}

# tb.gains = {
#     'ch00': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
#     'ch01': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
#     'ch02': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
#     'ch03': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
#     'ch04': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
#     'ch05': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
#     'ch06': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
#     'ch07': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
#     'ch08': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
#     'ch09': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
#     'ch10': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
#     'ch11': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
#     'ch12': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
#     'ch13': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
#     'ch14': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
#     'ch15': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
#     'ch16': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
#     'ch17': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
#     'ch18': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
#     'ch19': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
#     'ch20': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
#     'ch21': {'hg': 10.0, 'lg': 1.5, 'inCalib': None, 'enabled': True},
#     'ch22': {'hg': 10.0, 'lg': 1.5, 'inCalib': None, 'enabled': True},
#     'ch23': {'hg': 10.0, 'lg': 1.5, 'inCalib': None, 'enabled': True},
#     'ch24': {'hg': 10.0, 'lg': 1.5, 'inCalib': None, 'enabled': True},
#     'ch25': {'hg': 10.0, 'lg': 1.5, 'inCalib': None, 'enabled': True},
#     'ch26': {'hg': 10.0, 'lg': 1.5, 'inCalib': None, 'enabled': True},
#     'ch27': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
#     'ch28': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
#     'ch29': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
#     'ch30': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
#     'ch31': {'hg': 75.0, 'lg': 7.5, 'inCalib': None, 'enabled': True},
# }

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

sleep(1)

if getPedestals is False:
    tb.slowCtrl.flushRegisters(feedback=feedback)
    tb.startAcq()
    print("Acquisizione avviata!")

elapsedTime = 0

if dpcuRun is True:
    if getPedestals is True:
        tb.slowCtrl.startCAL(feedback=feedback)
        print("Calibrazione avviata!")

    tb.slowCtrl.startDPCURun()
    fileName = input("Inserire il nome del file "
                     "(senza estensione) su cui salvare i dati: ")

    t1 = perf_counter()

    tb.saveData(evtNum, fileName)

    tb.slowCtrl.stopDPCURun()
    
else:
    t1 = perf_counter()

    while input("Acquisizione in corso... Scrivere 'exit' per uscire\n\n > ") != "exit":
        continue

elapsedTime = perf_counter() - t1

if getPedestals is True:
    tb.slowCtrl.stopCAL(feedback=feedback)
    print("Calibrazione arrestata!")
else:
    tb.slowCtrl.stopACQ(feedback=feedback)
    print("Acquisizione arrestata!")

sleep(1)

tb.slowCtrl.powerOffCIT("all")
sleep(1)
print("Citiroc spenti!")

tbAlim.powerOffChannel(2)
print("Scheda spenta!")

tb.close()

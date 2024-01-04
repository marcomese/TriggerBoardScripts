# -*- coding: utf-8 -*-
"""
Created on Tue Sep  6 17:20:37 2022

@author: limadou
"""

import dpcuEmulatorLib as dpcuel
import alimLib as alm
from time import sleep, perf_counter

# trgMask = "0000000A"
# genericMask = "00000004"

trgMask = "00000002"
genericMask = None#"00000001"

evtNum = 600

feedback = True

dpcuRun = True

getPedestals = False

pedestalVal = "32643264"

threshold = 300

prescalerVals = [2,4,10,20]

alimAddr = 'USB0::0x0957::0x0F07::MY53004295::0::INSTR'
dpcuEmulatorAddr = '172.16.14.52'

tbAlim = alm.triggerBoardAlim(alimAddr)

tbAlim.powerOnChannel(2)
sleep(2)
print("Scheda trigger accesa!")

dpcu = dpcuel.dpcuEmulator(dpcuEmulatorAddr)

dpcu.powerOnCIT("cit0",feedback=feedback)
sleep(1)
print("Citiroc 0 acceso!")
dpcu.powerOnCIT("cit1",feedback=feedback)
sleep(1)
print("Citiroc 1 acceso!")

dpcu.changeChargeThreshold("all", threshold)
dpcu.changeTimeThreshold("all", threshold)
print(f"Soglie impostate a {threshold}")

dpcu.applyConfiguration("all",feedback=feedback)
sleep(1)
print("Citiroc configurati!")

for p in prescalerVals:

    dpcu.selectPrescaler(0,p,feedback=feedback)
    print("Prescaler M0 impostato!")
    
    dpcu.selectPrescaler(1,1,feedback=feedback)
    print("Prescaler M1 impostato!")
    
    dpcu.selectPrescaler(2,1,feedback=feedback)
    print("Prescaler M2 impostato!")
    
    dpcu.selectPrescaler(3,1,feedback=feedback)
    print("Prescaler M3 impostato!")
    
    dpcu.selectTriggerMask(trgMask,feedback=feedback)
    sleep(1)
    print(f"Maschera di trigger {trgMask} selezionata!")
    
    if genericMask is not None:
        dpcu.selectGenericTriggerMask(genericMask,feedback=feedback)
        print(f"Maschera di trigger generica {genericMask} selezionata!")
    
    dpcu.applyTriggerMask(feedback=feedback)
    sleep(1)
    print("Maschera di trigger applicata!")
    
    dpcu.changePedestal(pedestalVal, "all", feedback=feedback)
    sleep(1)
    
    if getPedestals is False:
        dpcu.flushRegisters(feedback=feedback)
        dpcu.writeRegVal("RST_REG","00000000")
        dpcu.startACQ(feedback=feedback)
        print("Acquisizione avviata!")
    
    elapsedTime = 0
    
    if dpcuRun is True:
        if getPedestals is True:
            dpcu.startCAL(feedback=feedback)
            print("Calibrazione avviata!")
    
        dpcu.startDPCURun()
        # fileName = input("Inserire il nome del file "
        #                  "(senza estensione) su cui salvare i dati: ")
        
        fileName = "prescalerTest_v1_4_7_OK"
    
        t1 = perf_counter()
    
        dpcu.saveDataStart(f"{fileName}-{p}",evtNum)
    
        dpcu.stopDPCURun()
        
        dpcu.getDataFile(f"{fileName}-{p}.dat", f"../{fileName}-{p}.dat")
    
    else:
        t1 = perf_counter()
    
        while input("Acquisizione in corso... Scrivere 'exit' per uscire\n\n > ") != "exit":
            continue
    
    elapsedTime = perf_counter() - t1
    
    print(f"Acquisizione finita, sono passati {elapsedTime:.3f} secondi")
    
    if getPedestals is True:
        dpcu.stopCAL(feedback=feedback)
        print("Calibrazione arrestata!")
    else:
        dpcu.stopACQ(feedback=feedback)
        print("Acquisizione arrestata!")
    
    sleep(1)

dpcu.powerOffCIT("all",feedback=feedback)
sleep(1)
print("Citiroc spenti!")

dpcu.close()

tbAlim.powerOffChannel(2)
print("Scheda spenta!")

tbAlim.close()
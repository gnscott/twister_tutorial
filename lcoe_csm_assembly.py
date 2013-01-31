"""
LCOE_csm_ssembly.py

Created by NWTC Systems Engineering Sub-Task on 2012-08-01.
Copyright (c) NREL. All rights reserved.
"""

import sys, os, fileinput
import numpy as np    

from openmdao.main.api import Component, Assembly, set_as_top, VariableTree, Slot
from openmdao.main.datatypes.api import Int, Bool, Float, Array

from twister.components.global_config import WESEConfig, get_dict

from twister.components.varTrees import Turbine, PlantBOS, PlantOM

# NREL cost and scaling model components for BOS, O&M, TCC and Finance
from twister.components.tcc_csm_component import tcc_csm_component
from twister.components.bos_csm_component import bos_csm_component
from twister.components.om_csm_component  import om_csm_component
from twister.components.fin_csm_component import fin_csm_component
# NREL cost and scaling model AEP assembly
from twister.assemblies.aep_csm_assembly import aep_csm_assembly

class lcoe_csm_assembly(Assembly):

    # ---- Design Variables ----------
    # See passthrough variables below
    # system input variables
    # turbine
    ratedPower = Float(5000.0, units = 'kW', iotype='in', desc= 'rated machine power in kW')
    rotorDiameter = Float(126.0, units = 'm', iotype='in', desc= 'rotor diameter of the machine')
    maxTipSpeed = Float(80.0, units = 'm/s', iotype='in', desc= 'maximum allowable tip speed for the rotor')
    drivetrainDesign = Int(1, iotype='in', desc= 'drivetrain design type 1 = 3-stage geared, 2 = single-stage geared, 3 = multi-generator, 4 = direct drive')
    hubHeight = Float(90.0, units = 'm', iotype='in', desc='hub height of wind turbine above ground / sea level')
    # plant
    seaDepth = Float(0.0, units = 'm', iotype='in', desc = 'sea depth for offshore wind project')
    altitude = Float(0.0, units = 'm', iotype='in', desc= 'altitude of wind plant')
    turbineNumber = Int(50, iotype='in', desc = 'total number of wind turbines at the plant')
    year = Int(2009, units = 'yr', iotype='in', desc = 'year of project start')
    month = Int(12, units = 'mon', iotype='in', desc = 'month of project start')    

    # ------------- Outputs -------------- 
    # See passthrough variables below

    def __init__(self,inputs=None):
        """ Creates a new LCOE Assembly object """

        super(lcoe_csm_assembly, self).__init__()
        
        # Assign inputs from user
        self.AssignInputs(inputs)
        
        #self.ofh = open('lcoeTrajectory.txt','w')

                
    def configure(self):
        ''' configures assembly by adding components, creating the workflow, and connecting the component i/o within the workflow '''

        # Create assembly instances (mode swapping occurs here)
        self.SelectComponents()

        # Set up the workflow
        self.WorkflowAdd()

        # Connect the components
        self.WorkflowConnect()
    
    def execute(self):

        #print "In {0}.execute()...".format(self.__class__)
        sys.stderr.write("In {0}.execute()...\n".format(self.__class__))

        super(lcoe_csm_assembly, self).execute()  # will actually run the workflow
        
        print 'LCOE {:7.5f} at diameter {:6.2f} m TS {:6.2f} mps'.format(self.lcoe, 
          self.rotorDiameter, self.maxTipSpeed)
        #self.ofh.write('LCOE {:7.5f} at diameter {:6.2f} m TS {:6.2f} mps\n'.format(self.lcoe, 
        #  self.rotorDiameter, self.maxTipSpeed))

        return self.lcoe  #TODO - output variable(s) should depend on user preference
        
    
    #------- Supporting methods --------------

    def SelectComponents(self):
        '''
        Component selections for wrapping different models which calculate main outputs for cost analysis
        '''

        aepa = aep_csm_assembly()
        self.add('aep1', aepa)

        tccc = tcc_csm_component()
        self.add('tcc', tccc)

        bosc = bos_csm_component()
        self.add('bos', bosc)

        omc = om_csm_component()
        self.add('om',  omc)

        finc = fin_csm_component()
        self.add('fin', finc)

    def WorkflowAdd(self):
        ''' modifies workflow to add the appropriate components '''

        self.driver.workflow.add(['aep1', 'tcc', 'bos', 'om', 'fin'])  

    def WorkflowConnect(self):
        ''' creates variable connections based on mode combinations - i/o between components depending on which models are selected '''

        # create passthroughs for key input variables of interest
        # turbine
        self.create_passthrough('tcc.bladeNumber')
        self.create_passthrough('tcc.advancedBlade')
        self.create_passthrough('tcc.thrustCoefficient')
        self.create_passthrough('aep1.maxPowerCoefficient')
        self.create_passthrough('aep1.optTipSpeedRatio')
        self.create_passthrough('aep1.cutInWindSpeed')
        self.create_passthrough('aep1.cutOutWindSpeed')
        self.create_passthrough('tcc.crane')
        self.create_passthrough('tcc.advancedBedplate')
        # plant
        self.create_passthrough('aep1.shearExponent')
        self.create_passthrough('aep1.windSpeed50m')
        self.create_passthrough('aep1.weibullK')
        self.create_passthrough('aep1.airDensity')
        self.create_passthrough('aep1.soilingLosses')
        self.create_passthrough('aep1.arrayLosses')
        self.create_passthrough('aep1.availability')
        self.create_passthrough('fin.fixedChargeRate')
        self.create_passthrough('fin.constructionTime')
        self.create_passthrough('fin.projectLifetime')

        # connect i/o to component and assembly inputs
        # turbine configuration
        # rotor
        self.connect('rotorDiameter', ['aep1.rotorDiameter', 'tcc.rotorDiameter', 'bos.rotorDiameter'])
        self.connect('maxTipSpeed', ['aep1.maxTipSpeed', 'tcc.maxTipSpeed'])
        self.connect('aep1.ratedWindSpeed', 'tcc.ratedWindSpeed')
        self.connect('aep1.maxEfficiency', 'tcc.maxEfficiency')
        # drivetrain
        self.connect('ratedPower', ['aep1.ratedPower', 'tcc.ratedPower', 'bos.ratedPower', 'om.ratedPower', 'fin.ratedPower'])
        self.connect('drivetrainDesign', ['aep1.drivetrainDesign', 'tcc.drivetrainDesign'])
        # tower
        self.connect('hubHeight', ['aep1.hubHeight', 'tcc.hubHeight', 'bos.hubHeight'])   
        # plant configuration
        # climate
        self.connect('altitude', ['aep1.altitude', 'tcc.altitude'])
        self.connect('seaDepth', ['tcc.seaDepth', 'bos.seaDepth', 'om.seaDepth'])
        # plant operation       
        self.connect('turbineNumber', ['aep1.turbineNumber', 'bos.turbineNumber', 'om.turbineNumber', 'fin.turbineNumber']) 
        # financial
        self.connect('year', ['tcc.year', 'bos.year', 'om.year'])
        self.connect('month', ['tcc.month', 'bos.month', 'om.month'])
        self.connect('tcc.turbineCost', ['bos.turbineCost', 'fin.turbineCost'])
        self.connect('aep1.aep', ['om.aep', 'fin.aep'])
        self.connect('bos.BOScost', 'fin.BOScost')
        self.connect('om.plantOM.preventativeMaintenanceCost', 'fin.preventativeMaintenanceCost')
        self.connect('om.plantOM.correctiveMaintenanceCost', 'fin.correctiveMaintenanceCost')
        self.connect('om.plantOM.landLeaseCost', 'fin.landLeaseCost')
 
        # create passthroughs for key output variables of interest
        # aep
        self.create_passthrough('aep1.ratedRotorSpeed')
        self.create_passthrough('aep1.ratedWindSpeed')
        self.create_passthrough('aep1.powerCurve')
        self.create_passthrough('aep1.aep')
        self.create_passthrough('aep1.aepPerTurbine')
        self.create_passthrough('aep1.capacityFactor')
        # tcc
        self.create_passthrough('tcc.turbineCost')
        self.create_passthrough('tcc.turbineMass')
        self.create_passthrough('tcc.turbine')
        # bos
        self.create_passthrough('bos.BOScost')
        self.create_passthrough('bos.plantBOS')
        # om
        self.create_passthrough('om.OnMcost')
        self.create_passthrough('om.plantOM')
        # fin
        self.create_passthrough('fin.lcoe')
        self.create_passthrough('fin.coe')

    def AssignInputs(self,inputs=None):

        if inputs != None:
            for key in inputs:
                self.inputs[key] = inputs[key]
        
            # assign inputs to variables for assembly
            for key in self.inputs:
                # Turbine configuration
                # rotor
                if key == 'rotorDiameter':
                    self.rotorDiam = float(self.inputs[key])
                if key == 'maxTipSpeed':
                    self.maxTipSpeed = float(self.inputs[key])
                if key == 'bladeNumber':
                    self.bladeNumber = int(self.inputs[key])
                if key == 'advancedBlade':
                    if int(self.inputs[key]) == 0:
                       self.advancedBlade = False
                    else:
                       self.advancedBlade = True
                if key == 'maxPowerCoefficient':
                    self.maxPowerCoefficient = float(self.inputs[key])
                if key == 'optTipSpeedRatio':
                    self.optTipSpeedRatio = float(self.inputs[key])
                if key == 'cutInWindSpeed':
                    self.cutInWindSpeed = float(self.inputs[key])
                if key == 'cutOutWindSpeed':
                    self.cutOutWindSpeed = float(self.inputs[key])
                if key == 'thrustCoefficient':
                    self.thrustCoefficient = float(self.inputs[key])
                # drivetrain
                if key == 'ratedPower':
                    self.ratedPower = float(self.inputs[key])
                if key == 'drivetrainDesign':
                    self.drivetrainDesign = int(self.inputs[key])
                if key == 'crane':
                    if int(self.inputs[key]) == 0:
                      self.crane = False
                    else:
                      self.crane = True
                if key == 'advancedBedplate':
                    self.advancedBedplate = int(self.inputs[key])
                # tower
                if key == 'hubHeight':
                    self.hubHeight = float(self.inputs[key])
                    
                # Plant configuration
                if key == 'windSpeed50m':
                    self.windSpeed50m = float(self.inputs[key])
                if key == 'weibullK':
                    self.weibullK = float(self.inputs[key])
                if key == 'shearExponent':
                    self.shearExponent = float(self.inputs[key])
                if key == 'seaDepth':
                    self.seaDepth = float(self.inputs[key])
                if key == 'altitude':
                    self.altitude = float(self.inputs[key])
                if key == 'airDensity':
                    self.airDensity = float(self.inputs[key])
                if key == 'year':
                    self.year = int(self.inputs[key])
                if key == 'month':
                    self.month = int(self.inputs[key])
                if key == 'turbineNumber':
                    self.turbineNumber = int(self.inputs[key])
                if key == 'soilingLosses':
                    self.soilingLosses = float(self.inputs[key])
                if key == 'arrayLosses':
                    self.arrayLosses = float(self.inputs[key])
                if key == 'availability':
                    self.availability = float(self.inputs[key])
                if key == 'discountRate':
                    self.discountRate = float(self.inputs[key])
                if key == 'taxRate':
                    self.taxRate = float(self.inputs[key])
                if key == 'discountRate':
                    self.discountRate = float(self.inputs[key])
                if key == 'constructionTime':
                    self.constructionTime = float(self.inputs[key])
                if key == 'projectLifetime':
                    self.projectLifetime = float(self.inputs[key])

#-------------------------------

    def printResults(self):
        print "LCOE: {0:7.4f}".format(self.lcoe)
        print "COE:  {0:7.4f}".format(self.coe)
        print "\n"
        print "AEP per turbine (kWh): {0:.2f}".format(self.aep / self.turbineNumber)
        print "Turbine Cost (USD):    {0:.2f}".format(self.turbineCost)
        print "BOS costs per turbine (USD): {0:.2f}".format(self.BOScost / self.turbineNumber)
        print "OnM costs per turbine (USD): {0:.2f}".format(self.OnMcost / self.turbineNumber)
        print
        print "Turbine output variable tree:"
        self.turbine.printVT()
        print
        print "Plant BOS output variable tree:"
        self.plantBOS.printVT()
        print
        print "Plant OM output variable tree:"
        self.plantOM.printVT()

#-------------------------------

    def printShortHeader(self):
        print '  LCOE      COE      AEP(mWh)     TCC(K$)     BOS(K$)      O&M(K$)'

    def printShortResults(self):
        ''' print one-line results with costs in K$ and AEP in mWh '''
        
        print " {0:8.5f}".format(self.lcoe),
        print " {0:8.5f}".format(self.coe),
        print " {0:10.5f}".format(0.001*self.aep / self.turbineNumber),
        print " {0:10.5f}".format(0.001*self.turbineCost),
        print " {0:10.5f}".format(0.001*self.BOScost / self.turbineNumber),
        print " {0:10.5f}".format(0.001*self.OnMcost / self.turbineNumber),
        print
        
if __name__=="__main__":

    lcoe = lcoe_csm_assembly()
    
    # modify default parameters with -rd, -ts, 
    
    for i in range(1,len(sys.argv)):
        arg = sys.argv[i]
        badArg = True
        if arg.startswith('-help'):
            sys.stderr.write(" USAGE: python {:} [-rdXXX] [-tsXXX] [-rpXXX] [-hhXXX] [-sdXXX]\n".format(sys.argv[0]))
            exit()
        if arg.startswith('-rd'):
            badArg = False
            try:
                lcoe.rotorDiameter = float(arg[3:])
                sys.stderr.write("  ...set rotorDiameter to {:.1f}\n".format(lcoe.rotorDiameter))
            except:
                sys.stderr.write("\nCan't understand '{:}'\n\n".format(arg))
        if arg.startswith('-ts'):
            badArg = False
            try:
                lcoe.maxTipSpeed = float(arg[3:])
                sys.stderr.write("  ...set maxTipSpeed to {:.1f}\n".format(lcoe.maxTipSpeed))
            except:
                sys.stderr.write("\nCan't understand '{:}'\n\n".format(arg))
        if arg.startswith('-rp'):
            badArg = False
            try:
                lcoe.ratedPower = float(arg[3:])
                sys.stderr.write("  ...set ratedPower to {:.1f}\n".format(lcoe.ratedPower))
            except:
                sys.stderr.write("\nCan't understand '{:}'\n\n".format(arg))
        if arg.startswith('-hh'):
            badArg = False
            try:
                lcoe.hubHeight = float(arg[3:])
                sys.stderr.write("  ...set hubHeight to {:.1f}\n".format(lcoe.hubHeight))
            except:
                sys.stderr.write("\nCan't understand '{:}'\n\n".format(arg))
        if arg.startswith('-sd'):
            badArg = False
            try:
                lcoe.seaDepth = float(arg[3:])
                sys.stderr.write("  ...set seaDepth to {:.1f}\n".format(lcoe.seaDepth))
            except:
                sys.stderr.write("\nCan't understand '{:}'\n\n".format(arg))
        
        if badArg:
            sys.stderr.write("\nUnrecognized argument '{:}'\n\n".format(arg))
                            
    lcoe.execute()
    lcoe.printShortHeader()
    lcoe.printShortResults()
    exit()
    
    # ---- Test 1 w/AdvBlade
    
    lcoe.advancedBlade = True
    lcoe.execute()
    
    #lcoe.printResults()
    lcoe.printShortHeader()
    lcoe.printShortResults()
    
    # ---- Test 2 w/NormalBlade
    
    lcoe.advancedBlade = False
    lcoe.execute()
    
    #lcoe.printResults()
    lcoe.printShortResults()
    
    # ---- Test 3 : some values of hubheight
    
    for hubht in np.arange(70.0,121.0,10.0):
        lcoe.hubHeight = hubht
        lcoe.execute()
        print '{:4.0f}m '.format(hubht),
        lcoe.printShortResults()
    
    #print dir(lcoe.lcoe)
    
    #print lcoe.lcoe.get_trait('units')
    #print lcoe.ratedPower.units
    
    #print "LCOE: {0:7.4f}".format(lcoe.lcoe)
    #print "COE:  {0:7.4f}".format(lcoe.coe)
    #print "\n"
    #print "AEP per turbine (kWh): {0:.2f}".format(lcoe.aep / lcoe.turbineNumber)
    #print "Turbine Cost (USD):    {0:.2f}".format(lcoe.turbineCost)
    #print "BOS costs per turbine (USD): {0:.2f}".format(lcoe.BOScost / lcoe.turbineNumber)
    #print "OnM costs per turbine (USD): {0:.2f}".format(lcoe.OnMcost / lcoe.turbineNumber)
    #print
    #print "Turbine output variable tree:"
    #lcoe.turbine.printVT()
    #print
    #print "Plant BOS output variable tree:"
    #lcoe.plantBOS.printVT()
    #print
    #print "Plant OM output variable tree:"
    #lcoe.plantOM.printVT()
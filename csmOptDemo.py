# csmOptDemo.py
# 2013 01 25
''' demonstrate optimization of LCOE '''

import sys, os, fileinput
from openmdao.main.api import Component, Assembly, set_as_top, VariableTree, Slot
from openmdao.lib.drivers.api import SLSQPdriver, CONMINdriver
from openmdao.lib.casehandlers.api import ListCaseRecorder

from lcoe_csm_assembly import lcoe_csm_assembly

global doplot, rpopt
doplot = True
#doplot = False
rpopt = False

try:
    import matplotlib.cm as cm
    import matplotlib.mlab as mlab
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
except:
    doplot = False
    sys.stderr.write("Couldn't find matplotlib - no plots will be generated\n")
    
#-----------------------------------------

class lcoeOpt(Assembly):
    """Unconstrained optimization of LCOE"""
    global doplot, rpopt

    def configure(self):

        # Create Optimizer instance
        self.add('driver', CONMINdriver())

        # Create LCOE instances
        self.add('lcoe', lcoe_csm_assembly())

        # Driver process definition
        self.driver.workflow.add('lcoe')

        self.driver.iprint = 0
        self.driver.iprint = 1
        self.driver.itmax = 30  # default is 10
        self.driver.dabfun = 0.00001 # default is.001
        self.driver.delfun = 0.001  # default is 0.1
        #self.driver.fdch = .0001
        #self.driver.fdchm = .0001   
             
        # Objective
        self.driver.add_objective('lcoe.lcoe')

        # Design Variables
        self.driver.add_parameter('lcoe.rotorDiameter', low=110., high=145.)
        if rpopt:
            self.driver.add_parameter('lcoe.ratedPower',    low=4500.,  high=5500.)
        else:
            self.driver.add_parameter('lcoe.maxTipSpeed',   low=75.,  high=100.)
        self.driver.case_outputs = ['lcoe.lcoe'] #,'lcoe.ratedPower','lcoe.maxTipSpeed'] 
          # lcoe.lcoe will be named 'Objective' in case recorder
        
        
        #Simple recorder which stores the cases in memory.
        self.driver.recorders = [ListCaseRecorder(),]
        
#-----------------------------------------

def main():
    
    global doplot, rpopt
    for i in range(1,len(sys.argv)):
        if sys.argv[i].startswith('-rp'):
            rpopt = True
    
    opt_problem = lcoeOpt()

    import time
    tt = time.time()

    opt_problem.run()

    print "\n"
    print 'Minimum found at ({:6.2f}m {:6.2f}mps)'.format(opt_problem.lcoe.rotorDiameter,
                                             opt_problem.lcoe.maxTipSpeed)
    print "Elapsed time: {:.2f} seconds".format(time.time()-tt)
    
    # show results of each case (as stored in caseRecorder)
    
    lcoeVals = []
    diamVals = []
    tipsVals = []
    rpwrVals = []
    for c in opt_problem.driver.recorders[0].get_iterator():
        print 'LCOE {:7.5f} at diameter {:6.2f} m '.format( 
            c['Objective'], c['lcoe.rotorDiameter']),
        if rpopt:
            print ' RP {:6.1f} kW'.format( c['lcoe.ratedPower']  )
            rpwrVals.append(c['lcoe.ratedPower'])
        else:
            print 'TS {:6.2f} mps'.format( c['lcoe.maxTipSpeed'] )
            tipsVals.append(c['lcoe.maxTipSpeed'])
            
        lcoeVals.append(c['Objective'])
        diamVals.append(c['lcoe.rotorDiameter'])
    
    if doplot:
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        
        if rpopt:
            yVals = rpwrVals
            ax.set_ylabel('Rated Pwr')
        else:
            yVals = tipsVals
            ax.set_ylabel('Tip Speed')    
            
        ax.plot(diamVals,yVals, zs=lcoeVals) # 3-d trajectory
        
        ax.scatter(diamVals[-1],yVals[-1], lcoeVals[-1], s=30, c='r') # final point
        
        # Plot the projection of the trajectory on the x/y plane
        
        #ax.plot(diamVals,tipsVals, zs=lcoeVals[-1]) # 2-d projection of trajectory
        lcoeMax = max(lcoeVals)
        lcoeMin = min(lcoeVals)
        ax.set_zlim3d(lcoeMin*0.98, lcoeMax*1.01)
        zlim = ax.get_zlim3d()
        ax.plot(diamVals,yVals, zs=zlim[0]) # 2-d projection of trajectory
        ax.scatter(diamVals[-1],yVals[-1], zlim[0], s=30, c='r') # final point
        
        plt.title("Optimization trajectory")
        ax.set_xlabel('Diameter')
        ax.set_zlabel('LCOE')
        ax.set_zlim3d(0.98*min(lcoeVals), 1.02*max(lcoeVals))
        plt.tight_layout()
        plt.savefig('optraj.png')
        sys.stderr.write('Saved plot file optraj.png\n')
        plt.show()
    
if __name__=="__main__":

    main()

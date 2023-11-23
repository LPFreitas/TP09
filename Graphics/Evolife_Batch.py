#!/usr/bin/env python3

""" @brief  Run Evolife without any display.
"""

#============================================================================#
# EVOLIFE  http://evolife.telecom-paris.fr             Jean-Louis Dessalles  #
# Telecom Paris  2023-11-19                                www.dessalles.fr  #
# -------------------------------------------------------------------------- #
# License:  Creative Commons BY-NC-SA                                        #
#============================================================================#
# Documentation: https://evolife.telecom-paris.fr/Classes                    #
#============================================================================#


##############################################################################
#  Batch mode                                                                #
##############################################################################



import os
import os.path
import sys

from time import sleep


from Evolife.Graphics import Simulation_Thread		# Thread to run the simulation in parallel

from Evolife.Tools.Tools import error
from Evolife.Graphics.Curves import Curves, EvolifeColourID	# names of curves



##################################################
# Simulation in batch mode (no vizualisation)    #
##################################################

class Evolife_Batch:
	""" Launches Evolife in a non-interactive way.
		Useful for repetitive simulation to explore parameter space.
	"""

	def __init__(self, SimulationStep, Obs):
		"""	Stores Obs as observer 
			and SimulationStep as the function that processes one step of the simulation.
			Creates curves from Obs's CurveNames.
		"""
		self.BestResult = None  # Best result returned from the simulation
		self.Results = []
		self.Curves = Curves()	# Stores curves
		self.Curves.Curvenames(Obs.get_info('CurveNames'))
		self.simulation = None  # name of the simulation thread
		self.Obs = Obs  # simulation observer
		self.OneStep = SimulationStep   # function that launches one step of the simulation


	def Simulation_stop(self):
		"""	Stops the simulation thread
		"""
		if self.simulation is not None:
			self.simulation.stop()
		
	def Simulation_launch(self,functioning_mode):
		"""	(re)starts the simulation thread
		"""
		self.Simulation_stop()
		self.simulation = Simulation_Thread.Simulation(self.OneStep, functioning_mode, self.ReturnFromThread)
		self.simulation.start()

	def ReturnFromThread(self, Best):
		""" The simulation thread returns the best current phenotype
		"""
		if Best == 'Buzy?':
			# this should never happen in batch mode
				error("Evolife_Batch","Inexistent buzy mode")
		self.BestResult = Best
		if self.Obs.Visible():
			self.Process_graph_orders(Best)
		if self.Obs.Over():
			return -1	# Stops the simulation thread
		else:
			return 0
					  
	def Process_graph_orders(self, BestPhenotype):
		"""	Retrieves plot orders from observer as a list of (CurveId, Point)
			and add points to curves accordingly
		"""
		for CurveData in self.Obs.get_info('PlotOrders'):
			(CurveId, Point) = CurveData[:2]
			try:
				self.Curves.Curves[EvolifeColourID(CurveId)[0]].add(Point)
			except IndexError:
				error("Evolife_Batch: unknown curve ID")
				
	def Destruction(self, event=None): 
		"""	Stops the simulation and dumps data into output file
		"""
		self.Simulation_stop()
		x_values_ignored = self.Obs.get_info('ResultOffset') # call first to make parameter 'relevant'
		self.Curves.Curvenames(self.Obs.get_info('CurveNames'))	# stores curve names - may have been updated	
		self.Curves.dump(self.Obs.get_info('ResultFile'), self.Obs.get_info('ResultHeader'), x_values_ignored)


##################################################
# Creation of the simulation thread              #
##################################################

def Start(SimulationStep, Obs):
	""" SimulationStep is a function that performs a simulation step
		Obs is the observer that stores statistics
	"""
	# No display, batch mode
	Evolife = Evolife_Batch(SimulationStep, Obs)
	Evolife.Simulation_launch(True)
	while True:
		sleep(5)
		if os.path.exists('stop'):
			Evolife.Simulation_stop()
			# os.remove('stop')
		if not Evolife.simulation.is_alive():
			break
	Evolife.Destruction()




__author__ = 'Dessalles'

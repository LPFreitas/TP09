#!/usr/bin/env python3

""" @brief  Simple trajectory display (here, Brownian movement).
"""

#============================================================================#
# EVOLIFE  http://evolife.telecom-paris.fr             Jean-Louis Dessalles  #
# Telecom Paris  2023-11-19                                www.dessalles.fr  #
# -------------------------------------------------------------------------- #
# License:  Creative Commons BY-NC-SA                                        #
#============================================================================#
# Documentation: https://evolife.telecom-paris.fr/Classes                    #
#============================================================================#


from random import randint	# for Brownian movement

import sys
sys.path.append('../..')

import Evolife.Graphics.Evolife_Window as EW
import Evolife.Ecology.Observer as EO
import Evolife.Graphics.Curves as EC

NBAGENTS = 4
MAXSTEP = 10

class Agent:
	"""	class Agent: defines what an individual consists of 
	"""
	def __init__(self, IdNb):
		self.ID = "A%d" % IdNb	# Identity number
		# basic colours are displayed at the right of Evolife curve display, from bottom up. Otherwise, use 'Shade'
		if IdNb % 2:	self.Colour = EC.Shade(IdNb, BaseColour='red', Max=NBAGENTS, darkToLight=False)
		else:			self.Colour = EC.Shade(IdNb, BaseColour='blue', Max=NBAGENTS)
		self.Size = 3
		self.CLocation = complex(50,50)

	def Location(self, NewLoc = None):
		if NewLoc is not None:
			self.CLocation.real, self.CLocation.imag = NewLoc[:2]
		return self.CLocation.real, self.CLocation.imag, self.Colour, self.Size

	def move(self, StepLoc=None):
		if StepLoc is None:
			# Just a Brownian movement
			step = randint(1,MAXSTEP)
			StepLoc = (randint(-step, step), randint(-step, step))
		NewCLoc = self.CLocation + complex(*StepLoc)
		# Coordinates:  (x, y, colour, size, toX, toY, segmentColour, segmentThickness)
		Segment = self.Location() + (NewCLoc.real, NewCLoc.imag, self.Colour, self.Size) 
		self.CLocation = NewCLoc
		return Segment
		
class Population:
	"""	defines the population of agents 
	"""
	def __init__(self, NbAgents, Observer):
		"""	creates a population of agents 
		"""
		self.Pop = [Agent(IdNb) for IdNb in range(NbAgents)]
		self.Obs = Observer
				 
	def __iter__(self):	return iter(self.Pop)	# allows to loop over Population
	
	#----------------------------------------------#	  
	# This function is run at each simulation step #	
	#----------------------------------------------#	  
	def one_year(self):
		self.Obs.StepId += 1	# updates simulation step in Observer
		for agent in self.Pop:	
			self.Obs.record(agent.move(), Window='Trajectories')
		return True

def Start():
	Obs = EO.Generic_Observer(TimeLimit=500)   # Observer stores graphic orders and performs statistics
	Obs.recordInfo('Title', "Trajectory display")

	# the following information will be displayed in the "Legend" window
	Obs.recordInfo('WindowLegends', """The "Trajectories" window shows agents' movements """)

	Obs.recordInfo('TrajectoriesWallpaper', '../../Evolife/Graphics/EvolifeBG.png')
	Obs.recordInfo('TrajectoriesTitle', 'Trajectories')
	
	# Evolife will start with this window open - sizes are in pixels
	# Obs.recordInfo('DefaultViews',	[('Trajectories', 300, 240)])	# just dimensions
	# Obs.recordInfo('DefaultViews',	[('Trajectories', 400, 200, 300, 240)])	# position and dimensions
	Obs.recordInfo('DefaultViews',	[('Trajectories', 400, 200, 300, 240, 0, 0, 0, 0)])	# Additional coordinates are margins
	
	Pop = Population(NbAgents=NBAGENTS, Observer=Obs)   # population of agents

	#--------------------------------------------------------------------------#
	# Start: launching Evolife window system                                   #
	#--------------------------------------------------------------------------#

	EW.Start(
		Pop.one_year, 	# this call-back function is called each year
		Obs, 	
		Capabilities='PT'	# means "photo" + "trajectory window"
		)
	

if __name__ == "__main__":
		print(__doc__)
		Start()
		print("Bye.......")


__author__ = 'Dessalles'

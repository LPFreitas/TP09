#!/usr/bin/env python3

""" @brief  This example shows how to use Evolife's graphic system (based on PyQT)
to run simulations that display images,dots and lines, and curves.

		-----------------------------------------------------------------------------------
		Evolife provides a window system that you can use for you own simulation.
	
		* Simulation:
		-	Re-implement the function 'One_Run' in the class 'Population'.
			This function is repeatedly called by Evolife. It should perform the simulation.
		-	This function typically executes individual behaviour: in this example, 
			function 'move'. You may just re-write the latter.
	
		* Display
		Evolife gets instructions for display through the class 'Observer'.
		Observer should return appropriate data to Evolife's requests, as indicated.
		This means that the simulation must keep Observer informed of relevant changes.
	
		* Starting Evolife
			Evolife can be started with various capabilities for display 
			(curves, dots and lines, genomes, links...) as indicated.
		-----------------------------------------------------------------------------------

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
# Example to show how to use Evolife's graphic system                        #
##############################################################################



	# Evolife's graphic system recognizes two forms of vectors
	# 
	#	- ((Agent1Id, Coordinates1), (Agent2Id, Coordinates2), ...)
	#	- (Coordinates1, Coordinates2, ...)
	# The first format allows to move and erase agents
	# The second format is merely used to draw permanent blobs and lines
	# Coordinates have the following form:
	#	(x, y, colour, size, ToX, ToY, segmentColour, segmentThickness, 'shape=<form>')
	#	(shorter tuples are automatically continued with default values - 'shape=...' can be inserted anywhere)
	# The effect is that an object of size 'size' is drawn at location (x,y) (your coordinates, not pixels)
	# and a segment starting from that blob is drawn to (ToX, ToY) (if these values are given)
	# If you change the coordinates of an agent in the next call, it will be moved.
	# 'size' is in pixels and is not resized in case of zoom. However, if negative, it is interpreted in your coordinates and it will be resized/
	# 'size' may be a fractional number. It is then understood as a fraction of the window size.
	# The value assigned to 'shape' in the string 'shape=...' can be 'ellipse' (=default) or 'rectangle' or
	# any image. If it is an image, 'colour' is interpreted as an angle. The image is scaled to fit 'size' (but aspect ratio is preserved)
	#
	# These two forms of vectors can be used to draw in two windows:  'Trajectories' and 'Field'.
	# Use the order:	record(vector, Window=<'Field'|'Trajectories'>)
	# or:				record([vectors], Window=<'Field'|'Trajectories'>)
	# 'Field' is default. The latter order is used to send a list of vectors.
	#
	# The 'Field' window comes in two modes, 'F' and 'R' (see below option F and R at Evolife's start)
	# 	- In the 'F' mode, all agents should be given positions at each call.
	# 	  Missing agents are destroyed from display.
	#	- In the 'R'  ('Region') mode, you may indicates positions only for relevant agents
	#	  To destroy an agent from display, give a negative value to its colour.




from time import sleep
from random import randint

import sys
sys.path.append('../..')

from Evolife.Graphics import Evolife_Window
from Evolife.Ecology import Observer
from Evolife.Graphics import Curves



class GrObserver(Observer.Generic_Observer):
	""" Stores all values that should be displayed
		May also store general information
	"""

	def __init__(self, TimeLimit):
		Observer.Generic_Observer.__init__(self, TimeLimit=TimeLimit)
		# declaration of a curve
		# Color should be one of Evolife's colours - See Curves.py
		self.curve(Name='Time', Color='blue', Legend='time step + noise')	# declaration of a curve
		# Then, to add a point to the curve, call:
		# curve('Time', y)
		# This adds a point (t, y) to the curve, where t is the current time step
		
		# the following information will be displayed in the "Legend" window
		self.recordInfo('WindowLegends', """The "field" window shows moving vectors.<br>The "Trajectories" window shows one rotating segment""")

	def Field_grid(self):
		"""	initial draw: here a green square 
		"""
		return [(5, 5, 'green', 5, 95, 5, 'green', 5),
				(95, 5, 'green', 5, 95, 95, 'green', 15),
				(95, 95, 'green', 5	, 5, 95, 'green', 5),
				(5, 95, 'green', 4, 5, 5, 'green', 5), ]		# 'green' becomes a curve, and '4' (last point size) here will be its eventual thickness in case of redraw
				# to draw lines with various dot sizes and segment thickness, name the segments
				# [(segm1, (5, 5, 'green', 8, 95, 5, 'green', 2)),
				#  (segm2, (95, 5, 'green', 5, 95, 95, 'green', 3),]
				# and be sure to use 'Region' instead of 'Field' when calling Evolife 'Start'
		
	def get_data(self, Slot):
		"""	This function is called each time the window wants to update display
		"""
		
		#--------------------------------------------------------------------------#
		# Displaying genomes	(option G when starting Evolife)                   #
		#--------------------------------------------------------------------------#
		if Slot == 'DNA':
			# Should return a list (or tuple) of genomes
			# Each genome is a tuple like (0,1,1,0,1,...)
			# All genomes should have same length
			pass
			
		#--------------------------------------------------------------------------#
		# Displaying social links	(option N (== network) when starting Evolife)  #
		#--------------------------------------------------------------------------#
		elif Slot == 'Network':
			# Should return a list (or tuple) of friends
			# 	((Agent1Id, Friends1), (Agent2Id, Friends2), ...)
			# Agents' Ids should be consistent with agents' positions sent to 'Field'
			# Friends = list of agents Ids to which the agent is connected
			# Currently, only links to best friends are displayed
			pass
			
		return Observer.Generic_Observer.get_data(self, Slot)	# default behaviour 

		#--------------------------------------------------------------------------#
		# Displaying images	(option F when starting Evolife)                       #
		#--------------------------------------------------------------------------#
		if Slot == 'Image':
			# Should return the path to an image file
			return default

		#--------------------------------------------------------------------------#
		# Displaying patterns (option T when starting Evolife)                     #
		# (same as slot 'Image', but for the 'Trajectories' window)                  #
		#--------------------------------------------------------------------------#
		elif Slot == 'Pattern':
			# Should return the path to an image file
			return default
			
		else:   return Observer.Generic_Observer.get_info(self, Slot, default=default)	# basic behaviour


class Agent:
	"""	class Agent: defines what an individual consists of 
	"""
	def __init__(self, IdNb):
		self.ID = "A%d" % IdNb	# Identity number
		# basic colours are displayed at the right of Evolife curve display, from bottom up. Otherwise, use 'Shade'
		if IdNb % 2:	self.colour = Curves.Shade(IdNb, BaseColour='red', Max=100, darkToLight=False)
		else:			self.colour = Curves.Shade(IdNb, BaseColour='blue', Max=100)
		self.Size = 5
		self.Location = (IdNb, randint(0, IdNb), self.colour, self.Size)	#  (x, y, colour, size)
	
	def move(self):	
		# Just a brownian vertical movement
		# Coordinates:  (x, y, colour, size, toX, toY, segmentColour, segmentThickness)
		self.Location = (self.Location[0], max(10, self.Location[1] + randint(-1, 1)), self.colour, self.Size, 50, 10, self.colour, 1)
		
class Population:
	"""	defines the population of agents 
	"""
	def __init__(self, NbAgents, Observer):
		"""	creates a population of agents 
		"""
		self.Pop = [Agent(IdNb) for IdNb in range(NbAgents)]
		self.Obs = Observer
		self.MouseEvent = None	# remembers mouse clicks
				 
	def __iter__(self):	return iter(self.Pop)	# allows to loop over Population
	
	def positions(self):
		return {A.ID:A.Location for A in self.Pop}
		
	#----------------------------------------------#	  
	# This function is run at each simulation step #	
	#----------------------------------------------#	  
	def one_year(self):
		self.Obs.StepId += 1	# updates simulation step in Observer
		for agent in self.Pop:	agent.move()		# whatever behaviour one wants to simulate
		
		# Storing agents' positions for display
		self.Obs.record(list(self.positions().items()), Window='Field')	# let Observer know position changes
		# Storing the ant's position for display
		self.Obs.record(('ant', (self.Obs.StepId % 80, 105, 0, 0.13, 'shape=ant.gif')), Window='Field')	# 0.13 == 13% of window size

		# display in window Trajectory
		self.Obs.record(('s1',(40 + 20*(((1+self.Obs.StepId) % 4)//2), 60 - 20 * ((self.Obs.StepId % 4)//2), 'brown', 1, 50, 50, 'brown', 3)), Window='Trajectories')


		# Displaying curve
		self.Obs.curve('Time', self.Obs.StepId + randint(0,20))	# draws noisy increasing line
		# Other syntax with explicit x-value:
		# self.Obs.curve('Time', (self.Obs.StepId, self.Obs.StepId + randint(0,20)))	# draws noisy increasing line
		
		MC = self.Obs.get_info('MouseClick', erase=True)
		if MC:
			self.MouseEvent = MC
			print(MC)
			self.Obs.record(('mouse', MC[1] + ('blue', 10)), 
				Window='Field' if MC[0] == 'Field_window' else 'Trajectories')

		
		return True
		

def Start():
	Obs = GrObserver(TimeLimit=10000)   # Observer stores graphic orders and performs statistics
	Obs.setOutputDir('___Results')	# curves, average values and screenshots will be stored there
	Obs.recordInfo('Background', 'yellow')	# windows will have this background by default
											# Background could be 'yellow' or 'toto.jpg' or '11' or '#F0B554'
	Obs.recordInfo('CurvesWallpaper', '../Graphics/EvolifeBG.png')
	Obs.recordInfo('TrajectoriesWallpaper', '../Graphics/EvolifeBG.png')
	Obs.recordInfo('TrajectoriesTitle', 'Trajectory window')
	Obs.recordInfo('FieldTitle', 'Field window')
	Obs.recordInfo('DefaultViews',	['Field', ('Trajectories', 300, 240)])	# Evolife should start with these windows open - these sizes are in pixels
	# other syntax for default views: ('Trajectories', 400, 600, 300, 240)
	
	
	Pop = Population(NbAgents=100, Observer=Obs)   # population of agents

	#--------------------------------------------------------------------------#
	# Start: launching Evolife window system                                   #
	#--------------------------------------------------------------------------#
	# Start(Callback function, Observer, Capabilities, Options)
	# Callback function:	this locally defined function is called by Evolife at each time step
	# Observer:	locally defined 
	# Capabilities: string containing any of the following letters
	#	C = Curves 
	#	F = Field (2D seasonal display) (excludes R)
	#	G = Genome display
	#	L = Log Terminal (not implemented)
	#	N = social network display
	#	P = Photo (screenshot)
	#	R = Region (2D ongoing display) (excludes F)
	#	T = Trajectory display (requires additional implementation in each case)

	Evolife_Window.Start(
		Pop.one_year, 
		Obs, 
		Capabilities='RCPT',
		Options = {'Run':True}
		)
	


if __name__ == "__main__":
		print(__doc__)
		Start()
		print("Bye.......")
		sleep(1.1)	


__author__ = 'Dessalles'

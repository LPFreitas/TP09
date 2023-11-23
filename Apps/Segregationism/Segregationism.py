#!/usr/bin/env python3
""" @brief  Emergence of segregationism:
Though individual agents show only slight preference for being surrounded by similar agent, homogeneous patches emerge.
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
# Segregationism (after Thomas Schelling's work)                             #
##############################################################################

# Thomas Schelling (1971) studied the dynamics of residential segregation
		# to elucidate the conditions under which individual decisions about where to live
		# will interact to produce neighbourhoods that are segregated by race.
		# His model shows that this can occur even though individuals do not act
		# in a coordinated fashion to bring about these segregated outcomes.
		# Schelling proposed a prototype model in which individual agents are of two types,
		# say red and blue, and are placed randomly on the squares of a checkerboard.
		# The neighbourhood of an agent is defined to be the eight squares adjoining his location.
		# Each agent has preferences over the composition of his neighbourhood,
		# defined as the proportion of reds and blues. In each period, the most dissatisfied
		# agent moves to an empty square provided a square is available that he prefers
		# to his current location. The process continues until no one wants to move.

		# The typical outcome is a highly segregated state, although nobody actually
		# prefers segregation to integration. 


import sys
from typing import List
sys.path.append('..')
sys.path.append('../../..')

import Evolife.Ecology.Observer				as EO
import Evolife.Scenarii.Parameters 			as EPar
import Evolife.Graphics.Evolife_Window 	as EW
import Evolife.Ecology.Individual			as EI
import Evolife.Ecology.Group				as EG
import Evolife.Ecology.Population			as EP
import Evolife.Graphics.Landscape			as Landscape


import random
# random.seed(4444)

Land = None	# to be instantiated
Observer = None	# to be instantiated

class Observer(EO.Observer):
	def Field_grid(self):
		# return  [(30,0,'#EEAA99',340, 30, 40, '#EEAA99', 340)]
		return  []

class Scenario(EPar.Parameters):
	def __init__(self):
		# Parameter values
		EPar.Parameters.__init__(self, CfgFile='_Params.evo')	# loads parameters from configuration file
		#############################
		# Global variables		    #
		#############################
		AvailableColours = ['red', 'blue', 'brown', 'yellow', 7] + list(range(8, 21))	# corresponds to Evolife colours
		self.Colours = AvailableColours[:self.Parameter('NbColours')]	
		self.addParameter('NumberOfGroups', self.Parameter('NbColours'))	# may be used to create coloured groups

class Individual(EI.Individual):
	""" Defines individual agents
	"""
	def __init__(self, Scenario, ID=None, Newborn=True):
		EI.Individual.__init__(self, Scenario, ID=ID, Newborn=Newborn)
		self.Colour = Scenario.Colours[0]	# just to initialize
		self.satisfied = False	# if false, the individual will move
		self.location = None

	def setColour(self, Colour):	
		self.Colour = Colour
		self.moves()	# gets a location

	def locate(self, NewPosition, Erase=True):
		"""	place individual at a specific location on the ground 
		"""
		if NewPosition is not None \
			and not Land.Modify(NewPosition, self.Colour, check=True): 	# new position on Land
			return False		 # NewPosition is not available  
		if Erase and self.location \
			and not Land.Modify(self.location, None): 	# erasing previous position on Land
			print('Error, agent %s badly placed' % self.ID)
		self.location = NewPosition
		self.display()
		return True

	def display(self):
		Observer.record((self.ID, self.location + (self.Colour, -1))) # for ongoing display on Field
		
	def decisionToMove(self):
		return not self.satisfaction()

	def satisfaction(self):
		self.satisfied = True	# default
		if self.location is None:	return False # may happen if there is no room left	
		Statistics = Land.InspectNeighbourhood(self.location, self.Scenario.Parameter('NeighbourhoodRadius'))	# Dictionary of colours
		# print(Statistics, end=' ')
		Same = Statistics[self.Colour]
		Different = sum([Statistics[C] for C in self.Scenario.Colours if C != self.Colour])	
		if (Same + Different) == 0:
			return self.satisfied
		if (Different / (Same + Different)) > self.Scenario.Parameter('Tolerance') / 100:
			self.satisfied = False
		return self.satisfied
	
	def measureNeighborhoodDiversity(self, point):
		Statistics = Land.InspectNeighbourhood(point, self.Scenario.Parameter('NeighbourhoodRadius'))
		Same = Statistics[self.Colour]
		Different = sum([Statistics[C] for C in self.Scenario.Colours if C != self.Colour])
		if (Same + Different) == 0:
			return 0
		return (Different / (Same + Different))
	
	def getBestPoint(self, potentialPointDiversityList):
		satisfiedPoints = [x for x in potentialPointDiversityList if x[1] <= self.Scenario.Parameter('Tolerance') / 100]
		if len(satisfiedPoints) == 0:
			# return min(potentialPointDiversityList, key=lambda x: x[1])[0]
			return random.choice(potentialPointDiversityList)[0]
		return random.choice(satisfiedPoints)[0]
	
	def decideWhereToMove(self):
		numEmptyPoints = self.Scenario.Parameter('LandSize')**2 - self.Scenario.Parameter('PopulationSize')
		SearchProportion = self.Scenario.Parameter('SearchProportion') / 100
		numOptions = max(int(SearchProportion * numEmptyPoints), 1)
		potentialPointDiversityList = []
		for i in range(numOptions):
			for ii in range(10): # should work at first attempt most of the time
				point = Land.randomPosition(Content=None, check=True)
				if point is None and ii == 0: 
					Land.statistics()
				if point is not None:
					potentialPointDiversityList.append((point, self.measureNeighborhoodDiversity(point)))
					break
		return self.getBestPoint(potentialPointDiversityList)

	def moves(self, Position=None):
		# print 'moving', self
		global Land
		if Position:
			return self.locate(Position)
		else:
			# pick a random location and go there (TO BE MODIFIED)
			for ii in range(10): # should work at first attempt most of the time
				# Landing = Land.randomPosition(Content=None, check=True)	# selects an empty cell
				Landing = self.decideWhereToMove()
				if Landing and self.locate(Landing):
					return True
				elif ii == 0:	Land.statistics()   # need to update list of available positions
			print("Unable to move to", Position)
			return False

	def __str__(self):
		return "(%s,%s) --> " % (self.ID, self.Colour) + str(self.location)

class Group(EG.Group):
	"""	The group is a container for individuals.
		Individuals are stored in self.members
	"""

	def __init__(self, Scenario, ID=1, Size=100):
		EG.Group.__init__(self, Scenario, ID, Size)
		self.Colour = None
		
	def setColour(self, Colour):
		self.Colour = Colour
		for member in self.members:	member.setColour(Colour)	# gives colour to all members
		
	def createIndividual(self, ID=None, Newborn=True):
		# calling local class 'Individual'
		Indiv = Individual(self.Scenario, ID=self.free_ID(), Newborn=Newborn)
		# Individual creation may fail if there is no room left
		# if Indiv.location == None:	return None
		return Indiv
		
	def satisfaction(self):	return 100 * sum([int(I.satisfied) for I in self]) / len(self) if len(self) else 100
	
class Population(EP.Population):
	"""	defines the population of agents 
	"""
	def __init__(self, Scenario, Observer):
		"""	creates a population of agents 
		"""
		EP.Population.__init__(self, Scenario, Observer)
		self.Colours = self.Scenario.Colours
		print(self.Colours)
		for Colour in self.Colours:
			print(f"creating {Colour} agents")
			# individuals are created with the colour given as ID of their group
			self.groups[self.Colours.index(Colour)].setColour(Colour)
		print(f"population size: {self.popSize}")
		self.Moves = 0  # counts the number of times agents have moved
		self.CallsSinceLastMove = 0  # counts the number of times agents were proposed to move since last actual move

	def createGroup(self, ID=0, Size=0):
		return Group(self.Scenario, ID=ID, Size=Size)

	def satisfaction(self):	return [(gr.Colour, gr.satisfaction()) for gr in self.groups]
	
	def One_Decision(self):
		""" This function is repeatedly called by the simulation thread.
			One agent is randomly chosen and decides what it does
		"""
		# EP.Population.one_year(self)	# performs statistics
		agent = self.selectIndividual()	# agent who will play the game	
		# print agent.ID, 'about to move'
		self.CallsSinceLastMove += 1
		if agent.decisionToMove() and agent.moves():
			self.Moves += 1
			self.CallsSinceLastMove = 0
		# if self.popSize:	self.Observer.season(self.Moves // self.popSize)  # sets StepId
		self.Observer.season()  # sets StepId
		# print(self.Observer.StepId)
		if self.Observer.Visible():	# time for display
			Satisfactions = self.satisfaction()
			for (Colour, Satisfaction) in Satisfactions:
				self.Observer.curve(Name=f'{Colour} Satisfaction', Value=Satisfaction)
			# if Satisfactions:
				# self.Observer.curve(Name='Global Satisfaction', Value=sum([S for (C,S) in Satisfactions])/len(Satisfactions))
	
		if self.CallsSinceLastMove > 10 * self.popSize:
			return False	# situation is probably stable
		return True	# simulation goes on


if __name__ == "__main__":
	print(__doc__)

	
	#############################
	# Global objects			#
	#############################
	Gbl = Scenario()
	Observer = Observer(Gbl)	  # Observer contains statistics
	Land = Landscape.Landscape(Gbl.Parameter('LandSize'))	  # logical settlement grid
	Land.setAdmissible(Gbl.Colours)
	Pop = Population(Gbl, Observer)   
	
	# Observer.recordInfo('Background', 'white')
	Observer.recordInfo('FieldWallpaper', 'white')
	Observer.recordInfo('DefaultViews',	[('Field', 400, 340), 'Legend'])	# Evolife should start with these windows open - these sizes are in pixels
	
	# declaration of curves
	for Col in Gbl.Colours:
		Observer.curve(Name=f'{Col} Satisfaction', Color=Col, Legend=f'average satisfaction of {Col} individuals')
	# Observer.curve(Name='Global Satisfaction', Color='black', Legend='average global satisfaction')
	
	EW.Start(Pop.One_Decision, Observer, Capabilities='RPC')

	print("Bye.......")
	
__author__ = 'Dessalles'
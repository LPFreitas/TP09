#!/usr/bin/env python3

""" @brief  (non-)Emergence of a convention such as car driving side
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
# (non-)Emergence of a convention such as car driving side                       #
##############################################################################

import sys
sys.path.append('..')
sys.path.append('../../..')

import Evolife.Ecology.Observer				as EO
import Evolife.Graphics.Evolife_Window 	as EW
import Evolife.Graphics.Landscape			as Landscape

import Segregationism as Seg

class Individual(Seg.Individual):
	""" Defines individual agents
	"""
	def moves(self, Position=None):
		"""	'Moving' in this scenario amounts to changing colour 
		"""
		if Position:
			self.locate(Position)
			return False	# doesn't change color
		elif self.location is None:
			super().moves(Position=Position)
			return False	# doesn't change color
		else:
			return True		# will change color

	
class Group(Seg.Group):
	"""	The group is a container for individuals. 
	"""
	def createIndividual(self, ID=None, Newborn=True):
		# calling local class 'Individual'
		Indiv = Individual(self.Scenario, ID=self.free_ID(), Newborn=Newborn)
		return Indiv

class Population(Seg.Population):
	"""	defines the population of agents 
	"""
	def createGroup(self, ID=0, Size=0):
		# calling local class 'Group'
		return Group(self.Scenario, ID=ID, Size=Size)

	def groupChange(self, agent):
		"""	moves a agent from a color group to another 
		"""
		agentColourNbr = self.Colours.index(agent.Colour)
		newColorNbr = 1 - agentColourNbr	# assuming only 2 colors
		self.groups[agentColourNbr].remove_member(agent)
		self.groups[newColorNbr].receive(agent)
		agent.Colour = self.Colours[newColorNbr]
		Seg.Land.Modify(agent.location, agent.Colour, check=False)

	def One_Decision(self):
		""" This function is repeatedly called by the simulation thread.
			One agent is randomly chosen and decides what it does
		"""
		agent = self.selectIndividual()	# agent who will play the game	
		if agent.decisionToMove() and agent.moves():
			self.groupChange(agent)	# agent switches to other group to change colour
			agent.display()
		year = self.Observer.season()  # sets StepId
		if self.Observer.Visible():	# time for display
			Satisfactions = self.satisfaction()
			for (Colour, Satisfaction) in Satisfactions:
				self.Observer.curve(Name='%s Satisfaction' % str(Colour), Value=Satisfaction)
			self.update()
		# MC = self.Observer.get_info('MouseClick', erase=True)
		# if MC and MC != 'erase':	print(MC)
			
		return True	# simulation goes on
			   

if __name__ == "__main__":
	print(__doc__)

	#############################
	# Global objects			#
	#############################
	Gbl = Seg.Scenario()
	Seg.Observer = EO.Observer(Gbl)	  # Seg.Observer contains statistics
	Seg.Land = Landscape.Landscape(Gbl.Parameter('LandSize'))	  # logical settlement grid
	Seg.Land.setAdmissible(Gbl.Colours)
	Pop = Population(Gbl, Seg.Observer)   
	
	# Seg.Observer.recordInfo('Background', 'white')
	Seg.Observer.recordInfo('FieldWallpaper', '#DDFFDD')
	Seg.Observer.recordInfo('DefaultViews',	[('Field', 400, 340), 'Legend'])	# Evolife should start with these windows open - these sizes are in pixels
	
	# declaration of curves
	for Col in Gbl.Colours:
		Seg.Observer.curve(Name='%s Satisfaction' % str(Col), Color=Col, Legend='average satisfaction of %s individuals' % str(Col))
	# Seg.Observer.curve(Name='Global Satisfaction', Color='black', Legend='average global satisfaction')
	
	EW.Start(Pop.One_Decision, Seg.Observer, Capabilities='RPC')

	print("Bye.......")
	
__author__ = 'Dessalles'

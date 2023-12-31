#!/usr/bin/env python3

""" @brief  This example shows how to use Evolife's to process a population
	structured in groups.
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
# Example to show how to use Evolife's ecology (population and groups)       #
##############################################################################

from time import sleep
from random import randint

import sys
sys.path.append('../..')
import Evolife.Ecology.Observer
import Evolife.Ecology.Population 
import Evolife.Ecology.Group
import Evolife.Ecology.Individual

class Scenario:
	def __init__(self):
		# mandatory parameters
		self.Params = dict()
		self.Params['PopulationSize'] = 20
		self.Params['NumberOfGroups'] = 3	# if more than one group: migrations occur
		self.Params['MigrationRate'] = 5

		# local parameters
		self.Params['TimeLimit'] = 10
		
	def Parameter(self, Param, Default='dummy'):
		if Param in self.Params:	return self.Params[Param]
		elif Default != 'dummy':	return Default
		print('Unknown parameter: %s' % Param)

	
class Individual(Evolife.Ecology.Individual.Individual):
	# we just change display
	
	def __str__(self):	return str(self.ID)	
	
class Group(Evolife.Ecology.Group.Group):
			
	def createIndividual(self, Id=None, Newborn=True):
		# calling local class 'Individual'
		return Individual(self.Scenario, Newborn=True, ID=self.free_ID())
		
	def remove_(self, IndivNbr):	
		# called when an agent migrates	
		print('%s migrates from group %d' % (self.members[IndivNbr], self.ID)	)
		return Evolife.Ecology.Group.Group.remove_(self, IndivNbr)

	def update_(self, flagRanking=False, display=False):
		self.size = len(self.members)
		return self.size

	def __str__(self):	return " ".join([str(ind) for ind in self.members])
			
#	-----------------------------------------------------------------------------------

class Population(Evolife.Ecology.Population.Population):

	def createGroup(self, ID=0, Size=0, Start=[]):
		# calling local class 'Group'
		return Group(self.Scenario, ID=ID, Size=Size)

	def statistics(self, Complete=True, Display=True):
		self.update()
		
	def __str__(self):
		self.update()
		return '\n'.join(['group %d:\t' % gr.ID + str(gr) for gr in self.groups]) + '\n________________\n\n'
		

		
def Start(Scenario, Population):
	for year in range(Scenario.Parameter('TimeLimit')):
		Population.one_year()
		print("\nYear %d" % year)
		print(Population)



if __name__ == "__main__":
	print(__doc__)
	
	Scen = Scenario()
	Obs = Evolife.Ecology.Observer.Generic_Observer()
	Pop = Population(Scen, Obs)
	
	Start(Scen, Pop)

	print("Bye.......")
	sleep(1.1)	


__author__ = 'Dessalles'

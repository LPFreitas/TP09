#!/usr/bin/env python3

""" @brief  This example shows how to use Evolife's genetic algorithm
	to run genetically based simulations .
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
# Example showing  how to use Evolife's genetic algorithm                    #
##############################################################################

from time import sleep
import sys
sys.path.append('../..')

import Evolife.Ecology.Observer		as EO
import Evolife.Ecology.Population 	as EP
import Evolife.Ecology.Group 		as EG
import Evolife.Ecology.Individual 	as EI
import Evolife.Scenarii.Default_Scenario	as EDefaultScenario
import Evolife.Graphics.Evolife_Window	# if one wants to use graphic



class Scenario(EDefaultScenario.Default_Scenario):
	###############################################################
	# reimplement here any function defined in "Default_Scenario" #
	###############################################################
	
	def evaluation(self, Indiv):
		Indiv.score(Indiv.gene_value('gene2'))
	
class Individual(EI.EvolifeIndividual):
	def __init__(self, Parameters, ID=None, Newborn=True):
		EI.EvolifeIndividual.__init__(self, Parameters, ID, Newborn)

	###############################################################
	# Add here any characteristcs or behaviour of individuals     #
	###############################################################

	def __str__(self):	return "%s" % (self.ID)
	
class Group(EG.EvolifeGroup):
	# The group is a container for individuals.
	# Individuals are stored in self.members
	
	def createIndividual(self, Newborn=True):
		# calling local class 'Individual'
		return Individual(self.Scenario, Newborn=Newborn)


class Population(EP.EvolifePopulation):
	# Individuals in the population are stored in a 'Group'
	def createGroup(self, ID=0, Size=0):
		# calling local class 'Group'
		return Group(self.Scenario, ID=ID, Size=Size)

	########################################################################
	# Add here any characteristcs or behaviour of the whole population     #
	########################################################################


#	-----------------------------------------------------------------------------------


		
def Start():
	Scen = Scenario('GAExemple', 'GA.evo')
	Obs = Evolife.Ecology.Observer.EvolifeObserver(Scen)
	Pop = Population(Scen, Obs)
	print('launching simulation')

	################################################################################
	# You may choose between the loop below and a call to Evolife's graphic system #
	################################################################################
	# for year in range(Scen.Parameter('TimeLimit')):
		# Pop.one_year()
		# print "\n\nYear %d" % year
		# print(Pop)
	Evolife.Graphics.Evolife_Window.Start(
		Pop.one_year, 
		Obs, 
		Capabilities='CGP'	# See "GraphicExample" for explanations
		)


if __name__ == "__main__":
	print __doc__
	
	Start()

	print "Bye......."
	sleep(1.1)	

__author__ = 'Dessalles'

#!/usr/bin/env python3

""" @brief 	 EVOLIFE: Cooperation Scenario:
		Individual A cooperates with individual B with the hope that
		B will reciprocate. A remembers B if it is the case.
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
#  S_Cooperation                                                             #
##############################################################################


#=============================================================#
	#  HOW TO MODIFY A SCENARIO: read Default_Scenario.py		 #
	#=============================================================#


import sys
if __name__ == '__main__':  sys.path.append('../..')  # for tests

import random

from Evolife.Tools.Tools import percent, noise_mult, error
from Evolife.Scenarii.Default_Scenario import Default_Scenario

######################################
# specific variables and functions   #
######################################

class Scenario(Default_Scenario):

	######################################
	# Most functions below overload some #
	# functions of Default_Scenario	  #
	######################################


	def genemap(self):
		""" Defines the name of genes and their position on the DNA.
		Accepted syntax:
		['genename1', 'genename2',...]:   lengths and coding are retrieved from configuration
		[('genename1', 8), ('genename2', 4),...]:   numbers give lengths in bits; coding is retrieved from configuration
		[('genename1', 8, 'Weighted'), ('genename2', 4, 'Unweighted'),...]:	coding can be 'Weighted', 'Unweighted', 'Gray', 'NoCoding'
		"""
		# vvvvvvvv  To be changed vvvvvvvv
		#-----------------------------------------------#
		# you might want to implement the reciprocity
		# scenario by considering two genes 'Cooperativeness' and
		# 'Reciprocity' that # control for g1 and g2 respectively
		#-----------------------------------------------#
		return ['Cooperativeness', 'Exploration'] # gene sizes are read from configuration (Starter, see Genetics section)
		# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

	def prepare(self, indiv):
		""" defines what is to be done at the individual level before interactions
			occur - Used in 'start_game'
		"""
		#   scores are reset
		indiv.score(200, FlagSet=True)	# resetting scores

		# friendship links (lessening with time) are updated 
		indiv.lessening_friendship((100 - self.Parameter('Erosion'))/100.0)
		indiv.detach()
		
			
	def partner(self, indiv, others):
		""" Selects the best memorized cooperator, if any.
			But with a probability controlled by the gene 'Exploration'
			another partner is randomly selected
		"""

		BF = indiv.best()	# best friend
		# if BF and BF not in others:
			# error('Cooperation: best friend has vanished',str(BF))
		# vvvvvvvv  To be changed vvvvvvvv
		#-----------------------------------------------#
		# In the reciprocity scenario, merely return BF 
		# if not None else choose randomly
		#-----------------------------------------------#
		if BF and random.randint(0,100) >= indiv.gene_relative_value('Exploration'):
			return BF
		# Exploration: a new partner is randomly chosen
		partners = others[:]	# ground copy of the list
		partners.remove(indiv)
		if BF in others:
			partners.remove(BF)
		if partners != []:
			return random.choice(partners)
		else:
			return None
		# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

	def interaction(self, indiv, Partner):
		""" Dyadic cooperative interaction: one player (indiv) makes the first step by
			offering a 'gift' to a partner. The latter then returns the favour.
			Both the gift and the returned reward are controlled by genes.
			Both involve costs.
		"""
		
		#   First step: initial gift
		gift = percent(self.Parameter('FirstStep') * indiv.gene_relative_value('Cooperativeness'))
		Partner.score(noise_mult(gift, self.Parameter('Noise')))	# multiplicative noise
		#   First player pays associated cost
		#   Cost is a function of investment
		cost = percent(gift * self.Parameter('FirstStepCost'))
		indiv.score(-cost)
		#   Receiver remembers who gave the gift
		# vvvvvvvv  To be changed vvvvvvvv
		Partner.follow(indiv, gift)	# Partner stores indiv in its address book
		#-----------------------------------------------#
		# you might want to implement the reciprocity
		# scenario by implementing the reciprocity behaviour instead
		#-----------------------------------------------#
		# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

		
	def update_positions(self, members, start_location):
		""" locates individuals on an 2D space
		"""
		# sorting individuals by gene value
		duplicate = members[:]
		duplicate.sort(key=lambda x: x.gene_value('Cooperativeness'))
		# vvvvvvvv  To be changed vvvvvvvv
		#-----------------------------------------------#
		# In the reciprocity scenario, 
		# you might want to display something else
		#-----------------------------------------------#
		for m in enumerate(duplicate):
			m[1].location = (start_location + m[0], m[1].gene_relative_value('Exploration'))

def wallpaper(self, Window):
	" displays background image or colour when the window is created "
	# Possible windows are: 'Field', 'Curves', 'Genome', 'Log', 'Help', 'Trajectories', 'Network'
	if Window == 'Curves':	return 'Scenarii/cooperation.jpg'
	return Default_Scenario.wallpaper(self, Window)

def display_(self):
	""" Defines what is to be displayed. It offers the possibility
		of plotting the evolution through time of the best score,
		the average score, and the average value of the
		various genes defined on the DNA.
		It should return a list of pairs (C,X)
		where C is the curve colour and X can be
		'best', 'average', any gene name as defined by genemap
		or any phene name as dedined by phenomap
	"""
	if self.Parameter('Correction') == 0:
		#-----------------------------------------------#
		# In the reciprocity scenario, 
		# you might want to display something else
		#-----------------------------------------------#
		#return [(2,'Cooperativeness'),(3,'Exploration'),(4,'average'),(5,'best')]
		return [('green','Cooperativeness'),('blue','Exploration')]
		# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

	# def remove_agent(self, agent):
		# " action to be performed when an agent dies "
		# print('removing', agent.ID)
		# pass


###############################
# Local Test                  #
###############################

if __name__ == "__main__":
	print(__doc__ + '\n')
	input('[Return]')
	

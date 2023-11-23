#!/usr/bin/env python3

""" @brief 	 A scenario to study the fate of favourable / unfavourable mutation.

		This the most basic Darwinian case.
		Also: allows to define the benefit at the group level, what allows
		the study of the so-called 'group selection'.
"""

#============================================================================#
# EVOLIFE  http://evolife.telecom-paris.fr             Jean-Louis Dessalles  #
# Telecom Paris  2023-11-19                                www.dessalles.fr  #
# -------------------------------------------------------------------------- #
# License:  Creative Commons BY-NC-SA                                        #
#============================================================================#
# Documentation: https://evolife.telecom-paris.fr/Classes                    #
#============================================================================#





	#=============================================================#
	#  HOW TO MODIFY A SCENARIO: read Default_Scenario.py		 #
	#=============================================================#


import sys
if __name__ == '__main__':  sys.path.append('../..')  # for tests


from Evolife.Scenarii.Default_Scenario import Default_Scenario
from Evolife.Tools.Tools import percent


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
		return ['favourable', 'neutral']  

	def initialization(self):
		self.CollectiveAsset = 0 # collective wealth due to group members
		self.Cumulative = bool(self.Parameter('Cumulative'))	# indicates whether scores are accumulated or are reset each year

	def start_game(self,members):
		""" defines what to be done at the group level each year
			before interactions occur - Used in 'life_game'
		"""

		if len(members) == 0:   return
		InitialBonus = 0
		
		# special case of negative benefits: Individuals are given an initial bonus to keep scores positive
		if self.Parameter('CollectiveBenefit') < 0:
			InitialBonus = -self.Parameter('CollectiveBenefit')		# just to keep scores positive
		if self.Parameter('IndividualBenefit') < 0:
			InitialBonus -= self.Parameter('IndividualBenefit')	# just to keep scores positive

		self.CollectiveAsset = 0	# reset each year

		for indiv in members:
			if self.Cumulative:	
				# Bonus is added to past score
				indiv.score(InitialBonus, FlagSet=False)
			else:
				# score is set to new value
				indiv.score(InitialBonus, FlagSet=True)	
			
			################################
			# computing collective benefit #
			################################
			# each agent contributes to collective benefit in proportion of its 'favourable' gene value
			self.CollectiveAsset += indiv.gene_relative_value('favourable')
		self.CollectiveAsset = float(self.CollectiveAsset) / len(members)

	def evaluation(self,indiv):
		""" Implements the computation of individuals' scores -  - Used in 'life_game'
		"""
		################################
		# computing individual benefit #
		################################
		IndividualValue = indiv.gene_relative_value('favourable')	# between 0 and 100
		# Bonus = <individual value> * <Individual benefit parameter> / 100 
		Bonus = percent(IndividualValue * self.Parameter('IndividualBenefit'))
		# Collective profit is merely added
		Bonus += percent(self.CollectiveAsset * self.Parameter('CollectiveBenefit'))
		indiv.score(Bonus, FlagSet=False)  # Bonus is added to Score 


	def update_positions(self, members, groupLocation):
		""" Allows to define spatial coordinates for individuals.
			These positions are displayed in the Field window.
		"""
		for indiv in enumerate(members):
			indiv[1].location = (groupLocation + indiv[0], indiv[1].score(), 4, -3)

	def default_view(self):
		""" Defines which windows should be open when the program starts
			Example: ['Genomes', 'Field', ('Trajectories', 320), ('Network', 500, 200)]
			optional numbers provide width and height
		"""
		return ['Genomes', ('*Field', 800, 500, 300, 300)]

	def wallpaper(self, Window):
		" displays background image or colour when the window is created "
		# Possible windows are: 'Field', 'Curves', 'Genome', 'Log', 'Help', 'Trajectories', 'Network'
		if Window == 'Curves':	return 'Scenarii/Landscape_.png'
		return Default_Scenario.wallpaper(self, Window)
		
	def display_(self):
		" Defines what is to be displayed. "
		return [('red','favourable'),('yellow','neutral')]


		
###############################
# Local Test                  #
###############################

if __name__ == "__main__":
	print(__doc__ + '\n')
	input('[Return]')
	

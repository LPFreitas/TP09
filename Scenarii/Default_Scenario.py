#!/usr/bin/env python3

""" @brief  Determines how individuals acquire their score, either by themselves or through interactions.

	Evolife scenarii may rewrite several functions defined here :
	(those marked with '+' are called from 'Group.py')
	(those marked with 'o' are called from 'Observer.py')

	- initialization(self): allows to define local variables
	- genemap(self):	initialises the genes on the gene map (see 'Genetic_map.py')
	- phenemap(self):   defines a list of phenotypic character names (see 'Phenotype.py')
	+ season(self, year, members):   makes periodic actions like resetting parameters
	+ behaviour(self, BestIndiv, AvgIndiv):   defines a behaviour to be displayed
	+ life_game(self, members): defines a round of interactions - calls the five following functions
		- start_game(self, members):	group-level initialization before starting interactions
			- prepare(self, indiv): individual initialization before starting interactions
		- interaction(self, Indiv, Partner):	defines a single interaction 
			- partner(self, Indiv, members):	select a partner among 'members' that will interact with 'Indiv'
		- end_game(self, members):  an occasion for a closing round after all interactions
		- evaluation(self, Indiv):  defines how the score of an individual is computed
		- lives(self, members): converts scores into life points
	+ couples(self, members): returns a list of couples for procreation (individuals may appear in several couples!)- Calls the following functions:
		- parenthood(self, RankedCandidates, Def_Nb_Children):	Determines the number of children depending on rank
		- parents(self, candidates):	selects two parents from a list of candidates (candidate = (indiv, NbOfPotentialChildren))
	+ new_agent(self, child, parents): initializes newborns
	+ remove_agent(self, agent): action to be performed when an agent dies
	+ update_positions(self, members, groupID):	assigns a position to agents
	o default_view(self): says which windows should be open at start up
	o legends(self): returns a string to be displayed at the bottom ot the Legend window.
	o display_(self):   says which statistics are displayed each year
	o def Field_grid(self):	initial draw in the Field window
	o def Trajectory_grid(self):	initial draw in the Trajectory window
	o wallpaper(self, Window):	if one wants to display different backgrounds in windows

						************
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
#  Scenarii                                                                  #
##############################################################################

	# This file shouldn't be edited - Rather edit particular scenarios #


import sys
if __name__ == '__main__':  sys.path.append('../..')  # for tests

import random

from Evolife.Scenarii.Parameters import Parameters
from Evolife.Genetics.Genetic_map import Genetic_map
from Evolife.Tools.Tools import decrease, chances

class Default_Scenario(Parameters, Genetic_map):
	"""	All functions defined here can be
		overloaded in specific scenarii (see module doc)
	"""
	def __init__(self, Name='Default scenario', CfgFile=''):
		"""	Loads parameters, sets gene map and calls local initialization. 
		"""
		self.Name = Name
		# loading parameter values
		if CfgFile == '':	CfgFile = self.Name + '.evo'
		try:	Parameters.__init__(self,CfgFile)
		except IOError:
			print("%s -- File not found." % CfgFile)
			CfgFile = 'Evolife.evo'
			print("Loading parameters from %s" % CfgFile)
			Parameters.__init__(self,CfgFile)

		# option for deterministic evolution
		if self.Parameter('RandomSeed', Default=0) > 0:	random.seed(Gbl.Parameter('RandomSeed'))
		
		# creating the genetic map
		Genetic_map.__init__(self, self.genemap())
		self.initialization()

	def initialization(self):
		"""	local initialization, to be overloaded 
		"""
		self.ALocalQuantity = 42 # a quantity that can be modified anywhere within the scenario

	def genemap(self):
		""" Defines the name of genes and their position on the DNA.
			Accepted syntax:
			- ['genename1', 'genename2',...]:   lengths and coding are retrieved from configuration.
			- [('genename1', 8), ('genename2', 4),...]:   numbers give lengths in bits; coding is retrieved from configuration.
			- [('genename1', 8, 'Weighted'), ('genename2', 4, 'Unweighted'),...]:	coding can be 'Weighted', 'Unweighted', 'Gray', 'NoCoding'.
			Note that 'Unweighted' is unsuitable to explore large space.
		"""
		return [('gene1',16),('gene2',4)]
		
	def phenemap(self):
		""" Defines the set of non inheritable characteristics
		"""
		# return ['Feature']
		return []
			
	def behaviour(self, best_individual, avg_individual):
		""" returns information about the phenotype of a given individual
			(best individual or fictitious individual with average genome)
			for display purposes  (e.g. a trajectory in a maze)
		"""
		return 0

	#######################################
	# The following functions are used    #
	# internally, called from 'life_game' #
	#######################################
	def prepare(self, indiv):
		""" defines what is to be done at the individual level before interactions
			occur - Used in 'start_game'
		"""
		pass
	
	def start_game(self, members):
		""" defines what is to be done at the group level each year
			before interactions occur - Used in 'life_game'
		"""
		for indiv in members:	self.prepare(indiv)

	def evaluation(self, indiv):
		""" Implements the computation of individuals' scores -  - Used in 'life_game'
		"""
		#Typically:  indiv.score(SOME VALUE, FlagSet=True)	 (FlagSet=False --> value is added to score instead of replacing it)
		# Note: scores should always be kept positive
		pass

	def partner(self, indiv, members):
		""" Decides whom to interact with - Used in 'life_game'
		"""
		# By default, a partner is randomly chosen
		partners = members[:]
		partners.remove(indiv)
		if partners != []:
			return random.choice(partners)
		else:
			return None
					
	def interaction(self, indiv, partner):
		""" Nothing by default - Used in 'life_game' 
		"""
		pass

	def end_game(self, members):
		""" defines what to do  at the group level once all interactions
			have occurred - Used in 'life_game'
		"""
		pass


	def life_game(self, members):
		""" Life games (or their components) are defined in specific scenarii
			life_games calls:
			- start_game (which calls 'prepare')
			- interaction (which calls 'partner')
			- end_game
			- evaluation
			- lives
		"""
		# First: make initializations
		self.start_game(members)
		# Then: play multipartite games
		for play in range(self.Parameter('Rounds', Default=1)):
			players = members[:]	# ground copy
			random.shuffle(players)
			# Individuals engage in several interactions successively
			for indiv in players:
				Partner = self.partner(indiv, players)
				if Partner is not None:
					self.interaction(indiv, Partner)
		# Lastly: work out
		self.end_game(members)
		# Alternatively (or successively): play individual games
		for indiv in members:
			self.evaluation(indiv)
		# scores are translated into life points
		self.lives(members)

	def lives(self, members):
		"""	converts scores into life points 
		"""
		if self.Parameter('SelectionPressure') == 0:
			return
		if len(members) == 0:
			return
		BestScore = max([i.score() for i in members])
		MinScore = min([i.score() for i in members])
		if BestScore == MinScore:	return
		for indiv in members:
			# translating scores to zero and above
			indiv.LifePoints = (self.Parameter('SelectionPressure') \
								* (indiv.score() - MinScore))/float(BestScore - MinScore)
		return

		
	def season(self, year, members):
		""" This function is called at the beginning of each year
		"""
		pass

	def parenthood(self, RankedCandidates, Def_Nb_Children):
		""" Determines the number of children that would-be parents may have 
			depending on their rank 
		"""
		candidates = [[m,0] for m in RankedCandidates]
		# parenthood is distributed as a function of the rank
		# it is the responsibility of the caller to rank members appropriately
		# Note: reproduction_rate has to be doubled, as it takes two parents to beget a child
		for Rank in range(len(RankedCandidates)):
			candidates[Rank][1] = chances(decrease(Rank, len(RankedCandidates),
											   self.Parameter('Selectivity')), 2 * Def_Nb_Children)
		# print()
		# print(self.Parameter('Selectivity'), 2 * Def_Nb_Children)
		# print([f"{decrease(ii,len(RankedCandidates), self.Parameter('Selectivity')):.3f}" for ii in range(len(RankedCandidates))])
		# print([chances(decrease(ii,len(RankedCandidates), self.Parameter('Selectivity')), 2 * Def_Nb_Children) for ii in range(len(RankedCandidates))])
		return candidates
	
	def parents(self, candidates):
		"""	Selects one couple from candidates.
			Candidates are (indiv, NbChildren) pairs, where NbChildren indicates the number of
			children that indiv can still have
		"""
		try:
			return random.sample(candidates, 2)
		except ValueError:	return None
		
	def couples(self, members, nb_children=-1):
		""" Returns a set of couples that will beget newborns.
			Note that a given individual may appear several times.
			By default, the probability for an individual to be in a
			couple (and thus to have a child) decreases with its rank
			in 'members'
		"""

		if nb_children < 0:		# the number of children may be imposed (e.g. in s_gazelle)
			nb_children = chances(self.Parameter('ReproductionRate') / 100.0, len(members))

		candidates = self.parenthood(members, nb_children)
		# print(candidates)

		Couples = []
		# print candidates[:10]
		for ii in range(nb_children):
			Couple = self.parents([p for p in candidates if p[1] > 0])	# selects two parents from the list of candidates
			if Couple:
				(mother, father) = Couple
				Couples.append((mother[0],father[0]))
				mother[1] -= 1
				father[1] -= 1
			else:	break
		return Couples

	def new_agent(self, child, parents):
		"""	initializes newborns - parents==None when the population is created
		"""
		return True
		 
		
	def remove_agent(self, agent):
		"""	action to be performed when an agent dies 
		"""
		pass
		
	def update_positions(self, members, groupLocation):
		""" Allows to define spatial coordinates for individuals.
			These positions are displayed in the Field window.
			Coordinates are typically (x,y,c) where c (optional)
			is the colour representing the agent
		"""
		for nbr, indiv in enumerate(members):
			indiv.location = (groupLocation + nbr, 17, 'red')

	def default_view(self):
		""" Defines which windows should be open when the program starts
			Example: ['Genomes', 'Field', ('Trajectories', 320), ('Network', 500, 200)]
			optional numbers provide width and height
		"""
		return []
		
	def legends(self):
		"""	The returned string will be displayed at the bottom ot the Legend window.
			Useful to describe what is to be seen in the various windows.
		"""
		L = '<u>Genomes</u>:<P>'
		L += 'genes from left to right: %s<br>' % (', '.join([g[0] if isinstance(g, tuple) else g for g in self.genemap()]))
		L += 'Each horizontal line represents the genome of an individual.'
		return L
		
	def display_(self):
		""" Defines what is to be displayed. It offers the possibility
			of plotting the evolution through time of the best score,
			the average score, any locally defined value,
			and the average value of the various genes and phenes.
			It should return a list of pairs (C, X) or triples (C, X, L)
			where C is the curve colour (colour name or number) 
			and X can be 'best', 'average', 'ALocalQuantity' 
			(where ALocalQuantity is a local variable)
			or any gene name defined in genemap 
			or any phene defined in phenemap.
			L (optional) is a legend string.
			Examples: 
				return ['gene1', 'gene2']
				return [('gene1', 'blue', 'evolution of gene1 through time'), ('gene2', 'orange', '')]
			Possibility of mentioning thickness:
				return [('gene1', 'blue', 'evolution of gene1 through time', 4), ('gene2', 'orange', '', 6)]
		"""
		# The default behaviour is to display all genes of GeneMap
		disp = [(i+1, G.name, f'Evolution of gene {G}') for (i, G) in enumerate(self.GeneMap)]
		
		# and all phenes of phenemap
		L = len(disp)
		disp += [(L+i+1, G, f'Evolution of phene {Ph}') for (i, Ph) in enumerate(self.phenemap())]

		# and a locally defined quantity
		# L = len(disp)
		# disp += [(L+1,'ALocalQuantity')]
		return disp
		
	def wallpaper(self, Window):
		""" Displays background image or colour when the window is created.
		"""
		# Possible windows are: 'Field', 'Curves', 'Genome', 'Log', 'Help', 'Trajectories', 'Network'
		if Window == 'Help':	return 'Graphics/EvolifeBG.png'
		return None
	
	def Field_grid(self):
		"""	returns a list of graphic orders for initial display on the Field window
		"""
		return []
		
	def Trajectory_grid(self):	
		"""	returns a list of graphic orders for initial display on the Trajectory window
		"""
		return []

	def __str__(self):
		return self.Name



###############################
# Local Test				  #
###############################

if __name__ == "__main__":
	print(__doc__ + '\n')
	input('[Return]')


__author__ = 'Dessalles'

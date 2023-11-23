#!/usr/bin/env python3

""" @brief  
	Evolution of martyrdom as a signal of one's patriotism,
	in presence of a motivated (admirative) audience
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
# version de Julien d'avril 2020
##############################################################################
# un peu nettoyée JLD 18.01.2023

from random import sample, shuffle, random, choice, randint
from math import exp, log
from time import sleep

import sys
sys.path.append('../../..')
import Evolife.Ecology.Observer	as EO
import Evolife.Ecology.Individual as EI
import Evolife.Ecology.Group as EG
import Evolife.Ecology.Population as EP
import Evolife.Scenarii.Default_Scenario as ED

from Evolife.Tools.Tools import percent, chances, decrease, error

class Scenario(ED.Default_Scenario):

########################################
#### General initializations and visual display ####
########################################
	def __init__(self):
		# Parameter values
		super().__init__(Name='Sacrifice', CfgFile='_Params.evo')	# loads parameters from configuration file

	def initialization(self):
		# called by __init__
		self.RememberedMartyrs = 0 # Nb of Martyrs that society "remembers" in a given round
		self.NewMartyrs = 0  # Nb of martyrs this year

	def genemap(self):
		""" Defines the name of genes and their position on the DNA.
		"""
		return [('Readiness')]
		#return [('SelfSacrifice')]  # gene length (in bits) is read from configuration
			### "Signal": le gene ne donne pas action auto / la meme pour tous

	def phenemap(self):
		""" Defines the set of non inheritable characteristics """
		return ['Patriotism']

	def display_(self):
		return [('blue', 'Readiness', 'Readiness to display patriotism'), 
				 ('black', 'RememberedMartyrs', 'Number of memorialized martyrs, normalized to 100'),
				 ('red', 'NewMartyrs', 'Percent of martyrs in a given year'),
				 ]
		
	def update_positions(self, members, groupLocation):
		for indiv in members:	
			indiv.location = (groupLocation + indiv.Phene_value('Patriotism'), 
				# indiv.Phene_value('Risk'), 'blue', 6)
				indiv.Reproductive_points, 'blue', 6)
	
	def new_agent(self, child, parents):
		child.inherit_share(parents[0],parents[1], heredity = percent(self.Parameter('SacrificeHeredity')))
		for P in parents: P.addChild(child)
		return True
		   
########################################
##### Life_game #### (1) Initializations ####
########################################
	def life_game(self, members):
		""" Light version of life_game with no interactions
		"""
		# First: make initializations
		self.start_game(members)	# calls 'prepare'
		# Lastly: work out
		self.end_game(members)
		# scores are translated into life points
		# self.lives(members)

	def prepare(self, indiv):
		""" Defines what is to be done at the individual level before interactions
			occur - Used in 'start_game'
		"""
		indiv.Reproductive_points = 100
		assert not indiv.SelfSacrifice

	def start_game(self, members):
		for indiv in members:
			for child in indiv.Children.copy():
				if not child in members:	# child is dead or moved to another group
					indiv.Children.remove(child)
		self.NewMartyrs = 0
		super().start_game(members)	# calls prepare


	def end_game(self, members):
		""" Sacrifice game. "Martyrs" are removed from the group
			and will not bear (additional) children.
		"""
		self.sacrifices(members)

########################################
##### Sacrifice game
########################################
			## (a) Individual propensity to self-sacrifice
	def deathProbability(self, indiv):
		""" Depending on an individual's patriotism
			and genetic readiness to display it,
			the individual may engage in self-sacrifice
		"""
		r = percent (indiv.gene_relative_value('Readiness')) \
			* percent (indiv.Phene_value('Patriotism'))
			
			### SENS PHYSIQUE vs visibilite ???
				### 2r = car moyenne pat = 1/2 //// r/5 = plus visible... -> 
		r = 2*r # So if all indiv have same readiness, average value is that
		#r = r/5 # pour comme JLD

		return r

	def selfSacrifice(self, indiv):
		""" An agent decides to make the ultimate sacrifice
			Her decision is predicated on her genetic 'readiness'
			and her phenotypic 'patriotism' (see above)
			Used in 'sacrifices'
		"""		
		p = self.deathProbability(indiv)
		## 'Probablistic' mode:
		bool = p > random() 

		# Other (unused) modes:
		## 'Binary mode': (Individuals are programmed to self-sacrifice at a certain age)
		#bool = p > 0 and (indiv.age > ((percent(self.Parameter('SacrificeMaturity')) * self.Parameter('AgeMax'))))
		## 'Threshold mode': gene codes for the value of the age after which sacrifice occurs
		# This is a measure of the 'value' of the sacrifice (how much potential reproduction is given up)
		#bool = indiv.age > (1-p) * self.Parameter('AgeMax')

		indiv.SelfSacrifice = bool
		return bool


########################################
			## (b) Population-level self-sacrifice game
	def sacrifices(self, members):
		""" Self-sacrifice 'game':
			Martyrs may self-sacrifice "for the good of the group"
			In return they are admired - admiration is exogenous here
			Used in 'life_game'
		"""
		Martyrs = []
		Cowards = members[:]
		for indiv in members:	# Deciding who are the population's Martyrs
			if self.selfSacrifice(indiv):	# indiv is not already a Martyr but is given an opportunity to be one
				Martyrs.append(indiv)
				Cowards.remove(indiv)

		self.NewMartyrs = len(Martyrs)

		random_Martyrs = 1 + int ( self.Parameter('PopulationSize') * (self.Parameter('MutationRate') / 1000 ) / self.Parameter('GeneLength'))
		#random_Martyrs = 0
		self.RememberedMartyrs = self.memo_Martyrs(len(Martyrs)-random_Martyrs, Cowards, 
									threshold = self.Parameter('RemThreshold'), 
									forget=self.Parameter('Forgetting'))	# modifies self.NewMartyrs
		
		self.inc_shares(Martyrs, Cowards)
	
		# In return, Martyrs are honored (admired) by society
		Admiration = self.honoring(Cowards, len(Martyrs))   
				
		self.spillover(Cowards, Admiration)
		self.kill_Martyrs(Martyrs)
		
		#return Cowards #Not used anymore
				### Utile si on veut "brancher" l'un sur l'autre...

	def memo_Martyrs(self, new_Martyrs, members, threshold = 5, forget=10):
		"""	Society, through its (alive)_ individuals, remembers its Martyrs
		"""
		
		#members.sort(key=lambda x: x.MartyrsWitnessed, reverse = True)
		#past_Martyrs = members[ int( percent(threshold) * len(members) )].MartyrsWitnessed   
		# Martyrs pass off to posterity if they are "remembered" by a sufficient amount of alive individuals
				#### Probablement bien trop couteux...
		
		### Option moins couteuse mais avec bcp plus de variance:
		Memorialists = sample(members, threshold)
		past_Martyrs = 0
		for memorialist in Memorialists:
			past_Martyrs += memorialist.MartyrsWitnessed
		past_Martyrs = past_Martyrs / threshold


		for indiv in members:
			indiv.HeroesWitnessed = int ( indiv.MartyrsWitnessed * (100.0 - forget) /100.0)
			# Added: indivs forget past heroes
					### A enlever ??? --- Au final autour de 5-10 des que >0 et selon si thresh/rdm (pour 10 + 25)
			indiv.MartyrsWitnessed += new_Martyrs
		self.NewMartyrs = 100.0 / self.Parameter('PopulationSize') * self.NewMartyrs # normalized to 100
		return 100.0 / self.Parameter('PopulationSize') * (past_Martyrs + new_Martyrs)

	def inc_shares(self, Martyrs, members):
		for Martyr in Martyrs: 
			# Childen, parents and siblings benefit from a Martyr's sacrifice:
			for indiv in members:
				if indiv in Martyr.Children:
					indiv.Share += 1
				if Martyr in indiv.Children:
					indiv.Share += 1
					for sibling in indiv.Children:
						if sibling == Martyr:
							pass
						else:
							sibling.Share += 1
			
	def honoring(self, audience, nb_Martyrs):
		""" Determines total 'social admiration' Martyrs may share
			Exogenous here, as a function of admiration.
			To be overloaded in two-tier (endogenous) model
		"""
		if nb_Martyrs == 0: return 0 # no Martyrs to admire this round

		### return self.Parameter('Admiration') * len(audience)

		admiration = 0
		for indiv in audience:
			indiv.Reproductive_points -= self.Parameter('Admiration')
			admiration += self.Parameter('Admiration')
		return admiration


	def spillover(self, members, admiration = 0):
		tot_share = sum([indiv.Share for indiv in members])
		if tot_share == 0:
			return
		for indiv in members:
			indiv.Reproductive_points += indiv.Share / tot_share * admiration
			
	def kill_Martyrs(self, Martyrs):
		for Martyr in Martyrs:
			#Martyr.score(-1, FlagSet = True)
			Martyr.LifePoints = -1


########################################
#### Reproduction ####
########################################
	def parenthood(self, Candidates, Nb_Children):
		""" Determines the number of children depending on reproductive points
			Selectivity is no longer used
		"""
		ValidCandidates = Candidates[:]
		tot_points = 1
		for Candidate in Candidates:
			tot_points += Candidate.Reproductive_points # test (devrait etre ap suicide)
			if Candidate.SelfSacrifice:
				ValidCandidates.remove(Candidate)	# Children and (dead) Martyrs cannot reproduce (AgeAdult is null by default)
		candidates = [[m,0] for m in ValidCandidates]
		#print(tot_points)
		total_children = 2 * Nb_Children
		for ParentID, Parent in enumerate(ValidCandidates):
			#candidates[ParentID[0]][1] = int(ParentID[1].Reproductive_points / 100.0 * (2 * Def_Nb_Children))
			#rem_children -= candidates[ParentID[0]][1]
			#rem_children = max(rem_children, 0)

				# Beaucoup trop grand ===> pas d'effet car tlm a 30 enfants (?)
			candidates[ParentID][1] = chances( Parent.Reproductive_points / tot_points, total_children)	# proportionality
			
		# Note: reproduction_rate NOT DOUBLED: cf article.

				### least worst option for now (pas 30 enfants par personne...) --  even though remH remains low

			#candidates[ParentID[0]][1] = chances(decrease(ParentID[1].Reproductive_points, tot_points, 1), 2 * Def_Nb_Children)
				### -> empty pop
		#print(candidates)
		return candidates




########################################
########################################
########################################

class Individual(EI.EvolifeIndividual):
	"   Defines what an individual consists of "

	def __init__(self, Scenario, ID=None, Newborn=True):
		self.SelfSacrifice = False
		self.MartyrsWitnessed = 0
		self.Reproductive_points = 100
		self.Share = 0
		self.Children = []
		EI.EvolifeIndividual.__init__(self, Scenario, ID=ID, Newborn=Newborn)

	def inherit_share(self, mom, dad, heredity = 0.5):
		self.Share += (mom.Share + dad.Share ) / 2 * heredity

	def isChild(self, Indiv):
		return Indiv in self.Children

	def addChild(self, child):
		" Adds child to list "
		self.Children.append(child)

	def removeChild(self, child):
		""" Removes a child of self
		Used when the child dies (see 'Group.remove_')
		"""
		if self.isChild(child):
			self.Children.remove(child)
	
########################################
########################################
########################################

class Group(EG.EvolifeGroup):
	""" The group is a container for individual (By default the population only has one)
		It is also the level at which reproduction occurs
		Individuals are stored in self.members
		Reproductive_points are used here to rank members for reproduction, not score
		(Selectivity)
	"""

	def __init__(self, Scenario, ID=1, Size=100):
		EG.EvolifeGroup.__init__(self, Scenario, ID, Size)

	def createIndividual(self, ID=None, Newborn=True):
		" Calling local class 'Individual'"
		return Individual(self.Scenario, ID=self.free_ID(Prefix=''), Newborn=Newborn)

	def update_ranks(self, flagRanking = False, display=False):
		""" updates various facts about the group
		"""
		# removing old chaps
		for m in self.members[:]:  # must duplicate the list to avoid looping over a modifying list
			if m.dead():	self.remove_(self.members.index(m))
			#if m.SelfSacrifice:	self.remove_(self.members.index(m)) # Martyrs die ################### ??
		self.size = len(self.members)
		if self.size == 0:	return 0
		# ranking individuals
		if flagRanking:
			# ranking individuals in the group according to their score
			self.ranking = self.members[:]	  # duplicates the list, not the elements
			self.ranking.sort(key=lambda x: x.Reproductive_points,reverse=True)
			if self.ranking != [] and self.ranking[0].Reproductive_points == 100:
				# all scores are 100
				shuffle(self.ranking)  # not always the same ones first
#			self.best_score = self.ranking[0].score()
		return self.size

	def update_(self, flagRanking = False, display=False):
		""" updates various facts about the group + positions
		"""
		size = Group.update_ranks(self, flagRanking=flagRanking)
		if display:
			if flagRanking:	self.Scenario.update_positions(self.ranking, self.location)
			else:			self.Scenario.update_positions(self.members, self.location)
		# updating social links
		for m in self.members:	m.checkNetwork(membershipFunction=self.isMember)
		return size

	def remove_(self, memberNbr):
		" An individual is removed from the group and his parents' family trees "
		indiv = self.whoIs(memberNbr)
		for parent in self.members:
			parent.removeChild(indiv)
		return EG.EvolifeGroup.remove_(self, memberNbr)

########################################
########################################
########################################

class Population(EP.EvolifePopulation):
	""" Defines the population of agents
		This is the level at which 'life_game' is played
	"""

	def createGroup(self, ID=0, Size=0):
		" Calling local class 'Group' "
		return Group(self.Scenario, ID=ID, Size=Size)

########################################
########################################
########################################

def Start(Gbl = None, PopClass = Population, ObsClass = None, Capabilities = 'PCGFN'):
	" Launch function "
	if Gbl == None: Gbl = Scenario()
	if ObsClass == None: Observer = EO.EvolifeObserver(Gbl)	# Observer contains statistics
	Pop = PopClass(Gbl, Observer)
	BatchMode = Gbl.Parameter('BatchMode')

	if BatchMode:
		import Evolife.Graphics.Evolife_Batch  as EB
		EB.Start(Pop.one_year, Observer)
	else:
		import Evolife.Graphics.Evolife_Window as EW
		EW.Start(Pop.one_year, Observer, Capabilities=Capabilities)
	if not BatchMode:	print("Bye.......")
	sleep(2.1)	
	return




if __name__ == "__main__":
	print(__doc__)

	#############################
	# Global objects			#
	#############################
	Gbl = Scenario()
	Start(Gbl)

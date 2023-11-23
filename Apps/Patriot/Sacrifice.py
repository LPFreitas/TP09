#!/usr/bin/env python3

""" @brief 	Could self-sacrifice therefore have a biological function? 
	This project sets the groundwork for investigating the (individual) biological motivations 
	that may underlie self-sacrifice (which need not coincide with its moral motivations, 
	potentially geared towards the collective).
"""


#============================================================================#
# EVOLIFE  http://evolife.telecom-paris.fr             Jean-Louis Dessalles  #
# Telecom Paris  2023-11-19                                www.dessalles.fr  #
# -------------------------------------------------------------------------- #
# License:  Creative Commons BY-NC-SA                                        #
#============================================================================#
# Documentation: https://evolife.telecom-paris.fr/Classes                    #
#============================================================================#



import sys
import random
import time	# for sleep

sys.path.append('../../..')
import Evolife.Ecology.Observer as EO
import Evolife.Ecology.Individual as EI
import Evolife.Ecology.Group as EG
import Evolife.Ecology.Population as EP
import Evolife.Scenarii.Default_Scenario as EDS
import Evolife.Genetics.Genome as EGenome	# for display

DEATHMEMORY = 500	# memory of recent death to compute life expectancy

class Scenario(EDS.Default_Scenario):
	""" Instantiating Default_Scenario.
	"""
	
	def __init__(self):
		super().__init__(Name='Sacrifice', CfgFile='___Sacrifice.evo') # loads 'Sacrifice.evo'
		
	def genemap(self):
		return ['K-Readiness']	# Readiness to become kamizaze
	
	def phenemap(self):
		"""	Defines the set of non inheritable characteristics
			Patriotism: consider sacrifice only if Patriotims exceeds genetic Readiness
			Risk:	used to store probability of commiting sacrifice
		"""
		return ['Patriotism', 'Risk']
			
	def initialization(self):
		# called by __init__
		self.NbSuicides = 0	# keeps track of suicides
		self.LifeExpectancy = 0	
		self.year = 0
		self.Deads = []
		
	def life_game(self, members):
		""" Light version of life_game with no interactions
		"""
		# First: make initializations
		self.start_game(members)	# calls 'prepare'
		# Lastly: work out
		self.end_game(members)
		# scores are translated into life points
		self.lives(members)
	
	def start_game(self, members):
		"""	Updating children and siblings
		"""
		for Parent in members:
			# print(Parent)
			for child in Parent.Children.copy():
				# ------ updating children's siblings
				for sibling in Parent.Children:
					if not sibling in members:	# sibling is dead or has moved
						continue
					if sibling != child:	
						child.Siblings.add(sibling)	
				# ------ updating parent's children
				if not child in members:	# child is dead or has moved
					Parent.Children.remove(child)
					continue
			assert not Parent.Hero
		self.NbSuicides = 0	# keeps track of suicides

	def end_game(self, members):
		# ------ decision to become a kamikaze
		KamikazeAge = self.Parameter('KamikazeAge') * self.LifeExpectancy / 100.0
		for indiv in members:
			# if Obs.Visible():	print('%d-%d' % (len(indiv.Children), len(indiv.Siblings)), end=' ', flush=True) 
			if indiv.suicide(KamikazeAge):	# most resolute individual may commit suicide
				# print('+', end="")
				self.NbSuicides += 1	# keeping track of suicides at the population level
		# ------ Benefits of being kin of kamikaze
		if self.NbSuicides > 0:
			bonus = (lambda B: (B * len(members) / self.NbSuicides) if self.Parameter('PrestigeSharing') else B)
			for indiv in members:
				if indiv.Hero:
					# ------ let children benefit from suicide
					for child in indiv.Children:
						child.KinOfHero = True	# for display
						child.score(bonus(self.Parameter('ChildrenBonus')))
						# print('\n', indiv, len(indiv.Children), '\n\t', str(child).replace('\n','\n\t'), flush=True)
					for sibling in indiv.Siblings:
						# sibling.KinOfHero = True	# for display
						sibling.score(bonus(self.Parameter('SiblingBonus')))
		if members:	self.NbSuicides /= len(members)	# from raw numbers to proportion
		self.NbSuicides *= 1000	# to get perthousand
		
	def season(self, year, members):
		""" This function is called at the beginning of each year
		"""
		self.year = year
		
	def lives(self, members):
		"""	converts scores into life points 
		"""
		super().lives(members)
		for indiv in members:
			# ------ Killing kamikazes
			if indiv.Hero:	
				indiv.LifePoints = -1
				pass
		return

	def new_agent(self, child, parents):
		"""	initializes newborns - parents==None when the population is created
		"""
		child.score(50, FlagSet=True)
		child.Phene_value('Risk', 
			child.Phene_value('Patriotism') * child.gene_relative_value('K-Readiness') / 100.0 / self.Parameter('GlobalRiskFactor'))
			# child.gene_relative_value('K-Readiness') / self.Parameter('GlobalRiskFactor'))
		if parents is None:	return True	# that's the case when the population is created from scratch
		for P in parents: 
			# make siblings aware of newborn
			for S in P.Children:
				child.Siblings.add(S)
				S.Siblings.add(child)
			# print(int(child.gene_relative_value('K-Readiness')), int(P.gene_relative_value('K-Readiness')), )
			# make parents aware of newborn
			P.Children.add(child)	# let know parents that their child is born
		return True
		 
	def remove_agent(self, agent):
		"""	action to be performed when an agent dies 
		"""
		# updating life expectancy
		if self.year < self.Parameter('DumpStart'):
			# print(f"{agent.age}({'+' if agent.Hero else '-'})", end='', flush=True)
			self.Deads.append(agent.age)
			self.Deads = self.Deads[-DEATHMEMORY:]
			# computing longevity median
			# self.LifeExpectancy = sum(self.Deads) / len(self.Deads)
			D = sorted(self.Deads)
			mid = len(D) // 2
			self.LifeExpectancy = (D[mid] + D[~mid]) / 2
		 
	def update_positions(self, members, groupLocation):
		for indiv in members:	
			color = 'red' if indiv.KinOfHero else 'blue'
			indiv.location = (
				groupLocation + indiv.Phene_value('Patriotism'), # x-coordinate
					# indiv.Phene_value('Risk'),
					indiv.score(),	# y-coordinate
				color, -2)

	def display_(self):
		return [('blue', 'K-Readiness', 'Genetic readiness to display patriotism', 4), 
				 # ('orange', 'Risk', 'Risk taking'),
				 ('red', 'NbSuicides', 'Percentage of suicides per year x 10'),
				 ('yellow', 'LifeExpectancy', 'Life expectancy'),
				 ]

	def Field_grid(self):	
		"""	draw frame in Field window
		"""
		# return [(0, 98, 'green', 1, 100, 98, 'green', 1), (100, 100, 1, 0)]
		return [(0, 98, 'green', 1), (100, 100, 1, 0)]
		
		
class Individual(EI.EvolifeIndividual):
	"""	defines an Evolife individual + aware of children and siblings
	"""

	def __init__(self, Scenario=None, ID=None, Newborn=False, maxQuality=100):
		super().__init__(Scenario=Scenario, ID=ID, Newborn=Newborn)
		# if not Newborn:	self.Phene_value('Patriotism', 100.0 * int(self.ID) / maxQuality) 
		self.Children = set()
		self.Siblings = set()
		self.Hero = False
		self.KinOfHero = False	# for display
		
	def suicide(self, KamikazeAge):
		# print(self.Phene_value('Risk'))
		# if (self.age > KamikazeAge) and (random.randint(0, 100) < self.Phene_value('Risk')):
		if self.age == int(KamikazeAge) and random.randint(0, 100) < self.Phene_value('Risk'):
			self.Hero = True
			# self.score(0, FlagSet=True)
			return True
		return False
	
	def __str__(self):
		return EI.EvolifeIndividual.__str__(self) + " --  Gen: " + EGenome.Genome.__str__(self)

class Group(EG.EvolifeGroup):
	"""	Calls local class when creating individuals
	"""
		
	def createIndividual(self, ID=None, Newborn=True):
		# calling local class
		Indiv = Individual(self.Scenario, ID=self.free_ID(Prefix=''), Newborn=Newborn)
		if not Newborn: self.Scenario.new_agent(Indiv, None)  
		return Indiv

		
class Population(EP.EvolifePopulation):
	"""	Calls local class when creating group
	"""

	def createGroup(self, ID=0, Size=0):
		# calling local class
		return Group(self.Scenario, ID=ID, Size=Size)	# local class

	def one_year(self):
		"""	Population's 'one_year' + calls to 'reproduction' and 'life_game' 
		"""
		if self.year >= 0:
			self.life_game()		# where individual earn their score
			self.reproduction()	 # reproduction depends on scores
		Res = EP.Population.one_year(self)	# by-passing EvolifePopulation.one_year
		return Res	

if __name__ == "__main__":
	Gbl = Scenario()
	Obs = EO.EvolifeObserver(Gbl)
	Pop = Population(Scenario=Gbl, Evolife_Obs=Obs)
	if Gbl['BatchMode']:
		import Evolife.Graphics.Evolife_Batch as EB
		EB.Start(SimulationStep=Pop.one_year, Obs=Obs)
	else:
		import Evolife.Graphics.Evolife_Window as EW
		print(__doc__)
	
		# launching windows
		# See Evolife_Window.py for details
		Capabilities='FGCP'	# F = 'Field'; G = 'Genomes'; C = 'Curves'; 
		Views = []
		if 'F' in Capabilities:	Views.append(('Field', 500, 350))	# start with 'Field' window on screen
		if 'T' in Capabilities:	Views.append(('Trajectories', 500, 350))	# 'Trajectories' on screen
		Obs.recordInfo('DefaultViews',	Views)	# Evolife should start with these window open
		EW.Start(SimulationStep=Pop.one_year, Obs=Obs, Capabilities=Capabilities, 
			Options=[('Background','green10')])
	time.sleep(1.1)


__author__ = 'Dessalles'

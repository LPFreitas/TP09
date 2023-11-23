#!/usr/bin/env python3

""" @brief  An Individual has a genome, several genes, a score and behaviours. """

#============================================================================#
# EVOLIFE  http://evolife.telecom-paris.fr             Jean-Louis Dessalles  #
# Telecom Paris  2023-11-19                                www.dessalles.fr  #
# -------------------------------------------------------------------------- #
# License:  Creative Commons BY-NC-SA                                        #
#============================================================================#
# Documentation: https://evolife.telecom-paris.fr/Classes                    #
#============================================================================#


##############################################################################
#  Individual                                                                #
##############################################################################


import sys
if __name__ == '__main__':  # for tests
	sys.path.append('../..')
	from Evolife.Scenarii.MyScenario import InstantiateScenario
	InstantiateScenario('SexRatio')


from random import randint

from Evolife.Genetics.Genome import Genome
from Evolife.Ecology.Phenotype import Phenome
from Evolife.Social.Alliances import Liker as Follower

class Individual:
	""" class Individual: basic individual.
		Just sets ID and age.
	"""

	def __init__(self, Scenario, ID=None, Newborn = True):
		self.Scenario = Scenario
		if not Newborn:
			# Aged individuals are created when initializing a population
			AgeMax = self.Scenario.Parameter('AgeMax', Default=100)
			self.age = randint(1, AgeMax)
		else:	self.age = 0
		if ID:
			self.ID = ID
		else:
			self.ID = 'A' + str(randint(0,9999)) # permanent identification in the population
		self.location = None   # location in a multi-dimensional space 
		self.__score = 0
		self.LifePoints = 0	  # some individuals may be more resistant than others

	def aging(self, step=1):
		"""	Increments the individual's age 
		"""
		self.age += step
		return self.age
		
	def accident(self, loss=1):
		"""	The victim suffers from a loss of life points 
		"""
		self.LifePoints -= loss
		
	def dead(self):
		"""	An individual is dead if it is too old or has lost all its 'LifePoints' 
		"""
		if self.LifePoints < 0:	return True
		AgeMax = self.Scenario.Parameter('AgeMax', Default=0)
		if AgeMax and (self.age > AgeMax):	return True
		return False		
	
	def dies(self):
		"""	Action to be performed when dying	
		"""
		pass
	
	def score(self, bonus=0, FlagSet=False):
		"""	Sets score or adds points to score, depending on FlagSet - Returns score value 
		"""
		if FlagSet:	self.__score = bonus
		else:		self.__score += bonus
		return self.__score

	def signature(self):
		"""	returns age and score 
		"""
		return [self.age, self.__score]

	def observation(self, GroupExaminer):
		"""	stores individual's signature in 'GroupExaminer' 
		"""
		GroupExaminer.store('Properties',self.signature())

	def display(self, erase=False):
		"""	can be used to display individuals 
		"""
		pass
	
	def __bool__(self):	
		# to avoid problems when testing instances (as it would call __len__ in Alliances)
		return True
		
	def __str__(self):
		# printing one individual 
		return "ID: " + str(self.ID) + "\tage: " + str(self.age) + "\tscore: " \
			   + "%.02f" % self.score()

				
				
				
class EvolifeIndividual(Individual, Genome, Phenome, Follower):
	"""	Individual + genome + phenome + social links 
	"""
	def __init__(self, Scenario, ID=None, Newborn=True, MaxFriends=0):
		"""	Merely calls parent classes' constructors 
		"""
		Individual.__init__(self, Scenario, ID=ID, Newborn=Newborn)
		if not Newborn:
			Genome.__init__(self, self.Scenario)
			Genome.update(self)  # gene values are read from DNA
		else:
			Genome.__init__(self, self.Scenario) # newborns are created with blank DNA
		Phenome.__init__(self, self.Scenario, FlagRandom=True)
		Follower.__init__(self, MaxFriends)

	def observation(self, GroupExaminer):
		"""	stores genome, phenome, social links and location into GroupExaminer 
		"""
		Individual.observation(self, GroupExaminer)
		GroupExaminer.store('Genomes', Genome.signature(self))
		GroupExaminer.store('DNA', list(self.get_DNA()), Numeric=True)
		GroupExaminer.store('Phenomes', Phenome.signature(self))
		GroupExaminer.store('Network', (self.ID, [T.ID for T in Follower.signature(self)]), Numeric=False)
		GroupExaminer.store('Field', (self.ID, self.location), Numeric=False)

	def dies(self):
		"""	Action to be performed when dying	
		"""
		Follower.detach(self)
		Individual.dies(self)
		
	def __str__(self):
		# printing one individual 
		return Individual.__str__(self) + "\tPhen: " + Phenome.__str__(self)
	
	
			
###############################
# Local Test                  #
###############################

if __name__ == "__main__":
	print(__doc__)
	print(Individual.__doc__ + '\n\n')
	John_Doe = Individual(7)
	print("John_Doe:\n")
	print(John_Doe)
	raw_input('[Return]')


__author__ = 'Dessalles'

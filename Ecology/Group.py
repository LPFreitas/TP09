#!/usr/bin/env python3

""" @brief	Groups are lists of Individuals.

Reproduction, selection and behavioural games
take place within the group.
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
#  Group                                                                     #
##############################################################################


import sys
if __name__ == '__main__':
	sys.path.append('../..')  # for tests
	from Evolife.Scenarii.MyScenario import InstantiateScenario
	InstantiateScenario('Cooperation')


from random import randint, sample, shuffle

from Evolife.Ecology.Individual import Individual, EvolifeIndividual
from Evolife.Ecology.Observer import Examiner		# for statistics
from Evolife.Tools.Tools import error

class Group:
	"""	A group is mainly a list of individuals 
	"""
	def __init__(self, Scenario, ID=1, Size=100):
		self.Scenario = Scenario	# Scenario just holds parameters
		self.size = 0
		self.members = []
		# ranking is used to store a sorted list of individuals in the group
		self.ranking = []   
		self.best_score = 0
		self.ID = ID
		self.location = 0   # geographical position 
		self.Examiner = Examiner('GroupObs'+str(self.ID))
		for individual in range(Size):
			Indiv = self.createIndividual(Newborn=False)
			self.receive(Indiv)
		self.update_(flagRanking=True)
		self.statistics()

	def free_ID(self, Prefix=None):
		"""	returns an available ID 
		"""
		IDs = [m.ID for m in self.members]
		for ii in range(100000):
			if Prefix is not None:	ID = '%s%d' % (Prefix, ii)
			else:		ID = '%d_%d' % (self.ID, ii)	# considering group number as prefix
			if ID not in IDs:	return ID
		return -1
			
	def createIndividual(self, ID=None, Newborn=True):
		"""	Calls the 'Individual' class 
		"""
		return Individual(self.Scenario, ID=self.free_ID(), Newborn=Newborn)

	def whoIs(self, Number):
		"""	Returns the Numberth individual 
		"""
		try:	return self.members[Number]
		except IndexError:	error('Group', 'selecting non-existent individual')

	def isMember(self, indiv):	return	indiv in self.members
	
	def update_(self, flagRanking = False, display=False):
		""" updates various facts about the group
		"""
		# removing old chaps
		for m in self.members[:]:  # must duplicate the list to avoid looping over a modifying list
			if m.dead():	
				self.remove_member(m)
		self.size = len(self.members)
		if self.size == 0:	return 0
		# ranking individuals
		if flagRanking:
			# ranking individuals in the group according to their score
			self.ranking = self.members[:]	  # duplicates the list, not the elements
			self.ranking.sort(key=lambda x: x.score(),reverse=True)
			if self.ranking != [] and self.ranking[0].score() == 0 and self.ranking[-1] == 0:
				# all scores are zero
				shuffle(self.ranking)  # not always the same ones first
			self.best_score = self.ranking[0].score()
		return self.size

	def statistics(self):
		""" Updates various statistics about the group.
			Calls 'observation' for each member
		"""
		self.Examiner.reset()
		self.Examiner.open_(self.size)
		for i in self.members:
			i.observation(self.Examiner)
		self.Examiner.close_()		# makes statistics for each slot

	def positions(self):
		"""	lists agents' locations 
		"""
		return [(A.ID, A.location()) for A in self.members]
		
	def season(self, year):
		"""	This function is called at the beginning of each year.
			Individuals get older each year
		"""
		for m in self.members:	m.aging()
		
	def kill(self, memberNbr):
		"""	suppress one specified individual of the group 
		"""
		# the victim suffers from an accident
		return self.remove_(memberNbr)
			
	def remove_(self, memberNbr):
		"""	tells a member it should die and then removes it from the group 
		"""
		indiv = self.whoIs(memberNbr)
		indiv.dies()	# let the victim know
		self.size -= 1
		return self.members.pop(memberNbr)
	
	def remove_member(self, indiv):
		"""	calls 'remove_' with indiv's index in the group 
		"""
		self.remove_(self.members.index(indiv))

	def extract(self, indiv):	
		"""	synonymous to 'remove_member' 
		"""
		return self.remove_member(indiv)
	
	def receive(self, newcomer):
		"""	insert a new member in the group 
		"""
		if newcomer is not None:
			self.members.append(newcomer)
			self.size += 1

	def __len__(self):	return len(self.members)
	
	def __iter__(self):	return iter(self.members)
	
	def __str__(self):
		"""	printing a sorted list of individuals, one per line 
		"""
		if self.ranking:	return ">\n".join(["%s" % ind for ind in self.ranking]) + "\n"
		else:				return "\n".join(["%s" % ind for ind in self.members]) + "\n"

		
		
class EvolifeGroup(Group):
	"""	class Group: list of individuals that interact and reproduce.
		Same as Group + reproduction + calls to Scenario functions.
	"""

	def createIndividual(self, Newborn=True):
		""" calls the 'EvolifeIndividual' class
			calls 'Scenario.new_agent'
		"""
		# Indiv = Group.createIndividual(self, Newborn=Newborn)
		Indiv = EvolifeIndividual(self.Scenario, ID=self.free_ID(), Newborn=Newborn)
		# let scenario know that there is a newcomer	
		if not Newborn: self.Scenario.new_agent(Indiv, None)  
		return Indiv

	def uploadDNA(self, Start):
		"""	loads given DNAs into individuals
		"""
		if Start:	
			# if len(Start) != self.size:
				# error("Group", "%d DNAs for %d individuals" % (len(Start), self.size))
			for m in self.members:
				m.DNAfill([int(n) for n in self.Start.pop(0).split()])
							
	def update_(self, flagRanking = False, display=False):
		""" updates various facts about the group + positions
		"""
		size = Group.update_(self, flagRanking=flagRanking)
		if display:
			if flagRanking:	self.Scenario.update_positions(self.ranking, self.location)
			else:			self.Scenario.update_positions(self.members, self.location)
		# updating social links
		for m in self.members:	m.checkNetwork(membershipFunction=self.isMember)
		return size
		
	def reproduction(self):
		""" reproduction within the group
			creates individuals from couples returned by 'Scenario.couples'
			by calling 'hybrid' on the parents' genome
			and then by mutating the individual and inserting into the group
		"""		
		# The function 'couples' returns as many couples as children are to be born
		# The probability of parents to beget children depends on their rank within the group
		self.update_(flagRanking=True)   # updates individual ranks
		for C in self.Scenario.couples(self.ranking):
			# making of the child
			# child = EvolifeIndividual(self.Scenario, ID=self.free_ID(), Newborn=True)			
			child = self.createIndividual(Newborn=True)			
			if child is not None:
				child.hybrid(C[0],C[1]) # child's DNA results from parents' DNA crossover
				child.mutate()
				child.update()  # computes the value of genes, as DNA is available only now
				if self.Scenario.new_agent(child, C):  # let scenario decide something about the newcomer
					self.receive(child) # adds child to the group

	def season(self, year):
		""" This function is called at the beginning of each year 
			It calls Scenario.season
		"""
		Group.season(self, year)
		self.Scenario.season(year, self.members)
		
	def kill(self, memberNbr):
		"""	kills or weakens one specified individual of the group 
		"""
		# the victim suffers from an accident
		indiv = self.whoIs(memberNbr)
		indiv.accident()
		if indiv.dead():	return self.remove_(memberNbr)
		return None
			
	def remove_(self, memberNbr):
		"""	calls Group.remove_ and also Scenario.remove_agent 
		"""
		indiv = self.whoIs(memberNbr)
		self.Scenario.remove_agent(indiv)   # let scenario know
		return Group.remove_(self, memberNbr)
		
	def life_game(self):
		"""	Calls Scenario.life_game 
		"""
		# Let's play the game as defined in the scenario
		self.Scenario.life_game(self.members)
		# life game is supposed to change individual scores and life points

	def get_average(self):
		"""	computes an average individual in the group 
		"""
		Avg_DNA = [int(round(B)) for B in self.Examiner.storages['DNA'].average]
		Avg = EvolifeIndividual(self.Scenario, Newborn=True)	# individual with average DNA (standard Evolife (dummy) individual
		Avg.DNAfill(Avg_DNA)
		return Avg
		
	def get_best(self):
		"""	returns the phenotype of the best or representative individual 
		"""
		return self.Scenario.behaviour(self.ranking[0], self.get_average())
	
			
###############################
# Local Test                  #
###############################

if __name__ == "__main__":
	print(__doc__)
	print(Group.__doc__ + '\n')
	gr_size = 10
	MyGroup = Group(1,gr_size)
	print(MyGroup)
	raw_input('[Return to continue]')
	for ii in range(22):
		MyGroup.life_game()
		MyGroup.update_(flagRanking = True)
		print("%d > " % ii)
		print("%.02f" % (sum([1.0*i.score() for i in MyGroup.members])/gr_size))
		print(MyGroup.Examiner)
		MyGroup.reproduction(MyScenario.Parameter('ReproductionRate'))
		while MyGroup.size > gr_size:
			MyGroup.kill(randint(0,MyGroup.size-1))
	#print toto
	raw_input('[Return to terminate]')
	
__author__ = 'Dessalles'

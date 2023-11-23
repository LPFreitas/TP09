#!/usr/bin/env python3

""" @brief  A basic framework to run social simulations.
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
import os.path
import random
import itertools as it
import re
from time import sleep

sys.path.append('../../..')	# to include path to Evolife

from Evolife.Scenarii import Parameters
from Evolife.Tools import Tools
from Evolife.Ecology import Observer
from Evolife.Social import Alliances
from Evolife.Ecology import Learner

DUMPSTATE = True

class Global(Parameters.Parameters):
	"""	Global elements, mainly parameters
	"""
	def __init__(self, ConfigFile='_Params.evo'):
		# Parameter values
		Parameters.Parameters.__init__(self, ConfigFile)
		self.Parameters = self	# compatibility
		self.ScenarioName = self['ScenarioName']
		# Definition of interactions
		self.Interactions = None	# to be overloaded

	def Dump_(self, PopDump, ResultFileName, DumpFeatures, ExpeID, Verbose=False):
		""" Saves agents' features (possibly including agents' distance to best friend)
		"""
		
		# ====== storing feature values 
		if DumpFeatures is None or len(DumpFeatures) == 0:	return
		FeatureValues = dict()
		for Feature in DumpFeatures:
			FeatureValues[Feature] = PopDump(Feature)
		
		# ====== Sniffing data structure
		Test = FeatureValues[DumpFeatures[0]]
		# OldStyle: [Feature, AgentOfLowestQuality' feature value, AgentOfNextQuality' feature value, ...]
		# NewStyle: [(Quality1, FeatureValue1), (Quality2, FeatureValue2), ...]
		OldStyle = (len(Test) > 2 and type(Test[1]) == str and re.match(r'[0-9\.]+', Test[1]))
		if OldStyle:
			Qualities = list(range(len(FeatureValues[Feature])-1))
			for Feature in DumpFeatures:
				FeatureValues[Feature] = FeatureValues[Feature][1:]
		else:	# not used
			Qualities = sorted([x[0] for x in Test])
			for Feature in DumpFeatures:
				Values = dict(FeatureValues[Feature])
				FeatureValues[Feature] = [Values[q] for q in Qualities]	# robust to duplicates
		
		DumpFileName = ResultFileName + '_dmp.csv'
		if Verbose:	print("Saving data to", DumpFileName)
		SNResultFile = open(DumpFileName, 'w')
		SNResultFile.write('#%s\n' % ExpeID)
		if OldStyle:
			for Feature in DumpFeatures:
				SNResultFile.write(f"{Feature};")
				SNResultFile.write(";".join(FeatureValues[Feature]))
				SNResultFile.write("\n")	  
		else:	#NewStyle, 	not used
			Records = zip(map(str, Qualities), *[FeatureValues[f] for f in DumpFeatures])
			SNResultFile.write("Quality;" + ";".join(DumpFeatures) + "\n")
			for R in Records:
				SNResultFile.write(";".join(R) + "\n")
		SNResultFile.close()
		
	# def Param(self, ParameterName):	return self.Parameters.Parameter(ParameterName)


class Social_Observer(Observer.Experiment_Observer):
	"""	Stores some global observation and display variables
	"""

	def __init__(self, Parameters=None):
		"""	Experiment_Observer constructor 
			+ declaration of an average social distance curve
			+ initialization of social links
		"""
		Observer.Experiment_Observer.__init__(self, Parameters)
		#additional parameters	  
		self.Alliances = []		# social links, for display
		if self.Parameter('AvgFriendDistance'):	
			self.curve('FriendDistance', Color='yellow', Legend='Avg distance to best friend')
		
	def get_data(self, Slot, Consumption=True):
		"""	Experiment_Observer's get_data + slot 'Network' that contains social links
		"""
		if Slot == 'Network':	return self.Alliances			# returns stored links
		return Observer.Experiment_Observer.get_data(self, Slot, Consumption=Consumption)

	def hot_phase(self):
		"""	The hot phase is a limited amount of time, controlled by the 'LearnHorizon' parameter,
			during which learning is faster.
		"""
		return self.StepId < self.TimeLimit * self.Parameter('LearnHorizon') / 100.0

class Social_Individual(Alliances.Friendship, Learner.Learner):
	"""	A social individual has friends and can learn
	"""

	def __init__(self, IdNb, features={}, maxQuality=100, parameters=None):
		"""	Initalizes social links and learning parameters
		""" 
		if parameters: 	self.Param = parameters.Param
		else:	self.Param = None	# but this will provoke an error
		self.ID = "A%d" % IdNb	# Identity number
		if self.Param('SocialSymmetry', default=False):
			Alliances.Friendship.__init__(self, self.Param('MaxFriends'), self.Param('MaxFriends'))
		else:
			Alliances.Friendship.__init__(self, self.Param('MaxFriends'), self.Param('MaxFollowers', default=self.Param('MaxFriends')))
		self.Quality = (100.0 * IdNb) / maxQuality # quality may be displayed
		# Learnable features
		Learner.Learner.__init__(self, features, MemorySpan=self.Param('MemorySpan'), AgeMax=self.Param('AgeMax'), 
							Infancy=self.Param('Infancy'), Imitation=self.Param('ImitationStrength'), 
							Speed=self.Param('LearningSpeed'), JumpProbability=self.Param('JumpProbability', 0),
							Conservatism=self.Param('LearningConservatism'), 
							LearningSimilarity=self.Param('LearningSimilarity'), 
							toric=self.Param('Toric'), Start=self.Param('LearningStart', default=-1))
		self.Points = 0	# stores current performance
		self.update()

	def Reset(self, Newborn=True):	
		"""	called by Learner at initialization and when born again
			Resets social links and learning experience
		"""
		Learner.Learner.Reset(self, Newborn=Newborn)
		self.reinit(Newborn=Newborn)
		self.update()
		
	def reinit(self, Newborn=False):	
		"""	called at the beginning of each year 
			sets Points to zero and possibly erases social links (based on parameter 'EraseNetwork')
		"""
		# self.lessening_friendship()	# eroding past gurus performances
		if Newborn or self.Param('EraseNetwork'):	self.forgetAll()
		self.Points = 0

	def update(self, infancy=True):
		""" updates values for display
		"""
		Colour = 'green%d' % int(1 + 10 * (1 - float(self.Age)/(1+self.Param('AgeMax'))))
		if infancy and not self.adult():	Colour = 'red'
		if self.Features:	y = self.Features[self.Features.keys()[0]]
		else:	y = 17
		self.location = (self.Quality, y, Colour, 2)


	def Interact(self, Partner):	
		"""	to be overloaded
		"""
		pass	
		return True

	def assessment(self):
		"""	Social benefit from having friends - called by Learning
			(to be overloaded)
		"""
		pass		
		
	def __str__(self):
		return "%s[%s]" % (self.ID, str(self.Features))

	def __repr__(self):
		return self.ID
	
	# __repr__ = __str__
		
class Social_Population:
	"""	defines a population of interacting agents 
	"""
	def __init__(self, parameters, NbAgents, Observer, IndividualClass=None, features={}):
		"""	creates a population of social individuals
		"""
		if IndividualClass is None:	IndividualClass = Social_Individual
		self.Features = features
		self.PopSize = NbAgents
		self.Pop = [IndividualClass(IdNb, maxQuality=NbAgents, features=features.keys(), 
					parameters=parameters) for IdNb in range(NbAgents)]
		self.Obs = Observer
		self.Param = parameters.Param
		self.NbGroup = parameters.Parameter('NumberOfGroups', Default=1)	# number of groups
				 
	def positions(self):	
		"""	returns the list of agents' locations
		"""
		return [(A.ID, A.location) for A in self]

	def neighbours(self, Agent):
		"""	Returns agents of neighbouring qualitied 
		"""
		AgentQualityRank = self.Pop.index(Agent)
		return [self.Pop[NBhood] for NBhood in [AgentQualityRank - 1, AgentQualityRank + 1]
				if NBhood >= 0 and NBhood < self.PopSize]
		  
	def FeatureAvg(self, Feature):
		"""	average value of Feature's value
		"""
		Avg = 0
		for I in self:	Avg += I.feature(Feature)
		if self.Pop:	Avg /= len(self.Pop)
		return Avg
	
	def FriendDistance(self):	
		"""	average distance between friends
		"""
		FD = []
		for I in self:	
			BF = I.best_friend()
			if BF:	FD.append(abs(I.Quality - BF.Quality))
		if FD:	return sum(FD) / len(FD)
		return 0
		
	def display(self):
		"""	Updates agents positions and social links for display.
			Updates average feature values for curves
		"""
		if self.Obs.Visible():	# Statistics for display
			for agent in self:
				agent.update(infancy=self.Obs.hot_phase())	# update location for display
				# self.Obs.Positions[agent.ID] = agent.location	# Observer stores agent location 
			# ------ Observer stores social links
			self.Obs.Alliances = [(agent.ID, [T.ID for T in agent.social_signature()]) for agent in self]
			self.Obs.record(self.positions(), Window='Field')
			self.display_curves()
			
	def display_curves(self):
		if self.Param('AvgFriendDistance'):	self.Obs.curve('FriendDistance', self.FriendDistance())
		Colours = ['brown', 'blue', 'red', 'green', 'white']
		for F in sorted(list(self.Features.keys())):
			self.display_feature(F)
	
	def display_feature(self, F):
		self.Obs.curve(F, self.FeatureAvg(F), 
				Color=self.Features[F][0], 
				Thickness = self.Features[F][1] if len(self.Features[F]) > 1 else None,
				Legend=f'Avg of {F}')

	def season_initialization(self):
		"""	tells agents to reinitialize each year
		"""
		for agent in self:	agent.reinit()
	
	def systematic_encounters(self, group=None, shuffle=True, NbInteractions=1):
		"""	organizing systematic encounters
		"""
		if group is None: group = self.Pop
		Pairs = list(it.product(group, repeat=2))	# cartesian product group x group
		if shuffle:	random.shuffle(Pairs)
		# warning: Python does not like to mix iter() with yield, so no return iter(Pairs)
		for ii in range(NbInteractions):	# normally NbInteractions == 1 
			for Player, Partner in Pairs:
				if Player != Partner:	yield Player, Partner

	def random_encounters(self, group=None, NbInteractions=1):
		"""	organizing random encounters
		"""
		if group is None: group = self.Pop
		# randomly picking interacting pairs
		for ii in range(NbInteractions):	# normally NbInteractions == 1 if systematic is True
			yield random.sample(group, 2)
		
	def interactions(self, group=None, NbInteractions=None, shuffle=True, systematic=False):
		"""	interactions occur within a group 
		"""
		if NbInteractions is None: NbInteractions = self.Param('NbInteractions', default=1)
		# for ii in range(NbInteractions):	# normally NbInteractions == 1 if systematic is True
		if systematic:
			for Player, Partner in self.systematic_encounters(group, shuffle=shuffle, NbInteractions=NbInteractions):
				Player.Interact(Partner)
		else:
			for Player, Partner in self.random_encounters(group, NbInteractions=NbInteractions):
				Player.Interact(Partner)
	
	def learning(self):
		"""	called at each 'run', several times per year 
		"""
		for agent in self:
			agent.assessment()	# storing current scores (with possible cross-benefits)
		for agent in self:	# now cross-benefits are completed
			agent.wins(agent.Points)	# Stores points for learning
		# ------ some agents learn
		Learners = random.sample(self.Pop, Tools.chances(self.Param('LearningProbability')/100.0, len(self.Pop)))	
		for agent in Learners:
			agent.Learns(self.neighbours(agent), hot=self.Obs.hot_phase())
			# agent.update()	# update location for display
				
	def One_Run(self):
		"""	This procedure is repeatedly called by the simulation thread.
			It increments the year through season().
			Then for each run (there are NbRunPerYear runs each year),
			interactions take place within groups
		"""
		# ====================
		# Display
		# ====================
		self.Obs.season()	# increments year
		# ====================
		# Interactions
		# ====================
		for Run in range(self.Param('NbRunPerYear')):	
			self.season_initialization()
			
			# ------ interactions within groups
			GroupLength = max(1, len(self.Pop) // self.NbGroup)
			if self.NbGroup > 1:
				Pop = self.Pop[:] 
				random.shuffle(Pop)
			else:	Pop = self.Pop
			for groupID in range(self.NbGroup):	# interaction only within groups
				group = Pop[groupID * GroupLength: (groupID + 1) * GroupLength]
				self.interactions(group)

			# ------ learning
			self.learning()

		self.display()
		return True	# This value is forwarded to "ReturnFromThread"

	def __len__(self):	return len(self.Pop)
		
	def __iter__(self):	return iter(self.Pop)

		
def Start(Params=None, PopClass=Social_Population, ObsClass=Social_Observer, DumpFeatures=None, Windows='FNC'):
	"""	Launches the simulation
	"""
	if Params is None:	Params = Global()
	Observer_ = ObsClass(Params)   # Observer contains statistics
	Observer_.setOutputDir('___Results')
	Views = []
	if 'Views' in Params: Views = Params['Views'].split('+')
	Windows = set(Windows)
	for V in Views:	Windows.add(V[0])
	Windows = ''.join(Windows)
	if 'Field' in Views or 'F' in Windows:	Views.append(('Field', 770, 70, 520, 370))
	# if 'N' in Windows:	Views.append(('Network', 530, 200))
	# if 'T' in Windows:	Views.append(('Trajectories', 500, 350))
	Observer_.recordInfo('DefaultViews',	Views)	# Evolife should start with that window open
	# Observer.record((100, 100, 0, 0), Window='Field')	# to resize the field
	Pop = PopClass(Params, Params['NbAgents'], Observer_)   # population of agents
	# if DumpFeatures is None:	DumpFeatures = list(Pop.Features.keys()) + ['DistanceToBestFriend']
	Observer_.recordInfo('DumpFeatures', DumpFeatures)
	BatchMode = Params['BatchMode']
	
	if BatchMode:
		from Evolife.Graphics import Evolife_Batch
		##########	##########
		# Batch mode
		####################
		# # # # for Step in range(Gbl['TimeLimit']):
			# # # # #print '.',
			# # # # Pop.One_Run()
			# # # # if os.path.exists('stop'):	break
		Evolife_Batch.Start(Pop.One_Run, Observer_)
	else:
		from Evolife.Graphics import Evolife_Window
		####################
		# Interactive mode
		####################
		"""	launching window 
		"""
		try:
			Evolife_Window.Start(Pop.One_Run, Observer_, Capabilities=Windows+'P', 
					 Options={'Background':Params.get('Background', 'lightblue')})
		except Exception as Msg:
			from sys import excepthook, exc_info
			excepthook(exc_info()[0],exc_info()[1],exc_info()[2])
			input('[Entree]')
		
	if DUMPSTATE:
		# saving population state
		Params.Dump_(Pop.Dump, Observer_.get_info('ResultFile'), Observer_.get_info('DumpFeatures'), 
						Observer_.get_info('ExperienceID'), Verbose = not BatchMode)

	if not BatchMode:	print("Bye.......")
	# sleep(2.1)	
	return
	


if __name__ == "__main__":
	Gbl = Global()
	if Gbl['RandomSeed'] > 0:	random.seed(Gbl['RandomSeed'])
	Start(Gbl)



__author__ = 'Dessalles'

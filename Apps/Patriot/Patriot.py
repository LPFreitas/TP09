#!/usr/bin/env python3

""" @brief  Study of the emergence of exagerated signals in the presence of gossip
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
sys.path.append('../../..')

import Evolife.Tools.Tools as ET
import Evolife.Social.Alliances as EA
import Evolife.Social.SocialSimulation as SSim

Gbl = None	# will hold global parameters

# When the 'PolicingProbability' feature is interpreted as binary (>< 50) and it isn't costly enough,
# random fluctuations may create policing artificially - So True seems preferrable.
GRADUALPOLICINGPROBABILITY	= True	# if True, the actual policing probability is a non-linear function of the feature
									# otherwise, it is a mere binary threshold above or below 0.5

	


class Observer(SSim.Social_Observer):
	def __init__(self, Parameters=None):
		if Gbl.Parameter('DrawCostline', Default=1):
			self.MaxCostCoeff = -Gbl['SignallingCost'] * \
				ET.decrease(Gbl['BottomCompetence'], 100, Gbl['CostDecrease'])
			self.MaxCostCoeff = int(self.MaxCostCoeff + 1 - 0.000001)
		super().__init__(Parameters)
		L = '<br><u>Field</u>:<br>'
		L += 'Individuals are displayed by the signal they emit as a function of their quality.<br>'
		L += 'Red dots are negative gossipers. Brown dots are gossipees.<br>'
		L += 'Orange dots are positive gossipers. Green dots are praised individuals.<br>'
		L += 'Blue shades get darker with gossiping probability. The green curve (if displayed) represents the cost coefficient.<br>'
		if Gbl.Parameter('DrawCostline', Default=1):
			L += 'Cost line in blue = cost coefficient ' + \
				(f'/ {self.MaxCostCoeff}' if self.MaxCostCoeff != 1 else '')
		L += '<br><u>Trajectories</u>:<br>'
		# L += "x-axis: signal -- y-axis: number of outrages directed at the individual<br>"
		L += "Policing probability of individuals ranked by quality<br>"
		self.recordInfo('WindowLegends', L)
		# self.recordInfo('Background', '#BBBBFF')

	def Field_grid(self):
		"""	initial draw: Maximal cost line 
		"""
		G = [(100, 100, 1, 0)]	# G = list of grid coordinates
		# ====== drawing cost line
		if Gbl.Parameter('DrawCostline', Default=1):
			# G = [(0, 0, 'blue', 1, 100, 100, 'blue', 1), (100, 100, 1, 0)]
			Dots = [(x, -100 * Gbl['SignallingCost'] * ET.decrease(x, 100, Gbl['CostDecrease']) / self.MaxCostCoeff,
					'green', 1) for x in range(Gbl['BottomCompetence'], 100) ]
			# print([int(D[1] * self.MaxCostCoeff) for D in Dots])
			G += [x+y for (x,y) in zip(Dots[:-1], Dots[1:])]
		# ====== drawing signal levels
		for sl in Gbl['Levels']:	G += [(0, sl, 'blue', 1, 100, sl, 'blue', 1)]
		return G
		
	
class Individual(SSim.Social_Individual):
	"""	class Individual: defines what an individual consists of 
	"""
	def __init__(self, IdNb, maxQuality=100, features={}, parameters=None):
		self.color = None
		self.top = False	# indicates that self signals at the top level
		self.BestSignal = 0	# best signal value in memory (for display)
		# self.GossipOpportunities = 0       # players' opportunities to gossip others may be capped
		
		# ====== memory of other individuals that might be admired:
		self.reputable = EA.Liker(Gbl['SocialMemory']) 
		self.praises = 0	# counts praises directed toward self (for display)
		
		# ====== memory of other individuals that might be despised:
		# self.disreputable = EA.Friend(Gbl['MaxFollowers']) 
		self.disreputable = EA.Liker(Gbl['SocialMemory']) 
		self.outrages = 0	# counts outrages directed toward self (for display)
		
		# ====== memory of other individuals that appear as pairs:
		# self.pairs = EA.Liker(Gbl['SocialMemory']) 
		
		# ====== Possibility of storing individuals whose signal has been seen or has not been seen
		self.ObservationMemory = set()
		if Gbl['SignalAmbiguity']:
			self.opaques = []
		
		# ====== Social_Individual includes friendship relations:
		SSim.Social_Individual.__init__(self, IdNb, features=features, maxQuality=maxQuality, parameters=Gbl)	# calls Reset()
		
		# ====== recalibrate quality
		BQ = Gbl['BottomCompetence']
		Q = (100 * IdNb) // maxQuality
		self.Quality = (100 - BQ) * Q // 100 + BQ
		
	def reinit(self, Newborn=False):	
		"""	called at the beginning of each year 
		"""
		if Newborn or Gbl['EraseNetwork']:	
			self.cleanMemory()
		self.Points = 0
		self.signal = None
		# ====== Non-linearity on policing probability to avoid parasitic policing
		# self.PolicingProbability = (self.feature('PolicingProbability')/100) ** 4
		self.PolicingProbability = ET.logistic(self.feature('PolicingProbability'), Steepness=1.1)
		self.activePolicing = self.Policing()
		self.MonitoringProbability = ET.logistic(self.feature('MonitoringProbability'))
		self.activeMonitoring = self.Monitoring()
		self.outrages = 0	# counts outrages directed toward self (for display)

	def cleanMemory(self):
		self.forgetAll()
		self.reputable.detach()
		self.disreputable.detach()
		# self.pairs.detach()
		self.top = False
		self.praises = 0	# counts praises directed toward self (for display)
		self.ObservationMemory = set()
		if Gbl['SignalAmbiguity']:	self.opaques = []
	
	def Colour(self):
		# return max(10, 17 - int(self.PolicingProbability * 7.0))
		return max(34, 41 - int(self.PolicingProbability * 7.0))

	def update(self, infancy=True):
		"""	Updating individual's data for display 
		"""
		if self.color is None:	self.color = self.Colour()
		# if infancy and not self.adult():	self.color = 'white'	# children are white
		self.BestSignal = self.bestFeatureRecord('Signal')
		if self.BestSignal is None:	self.BestSignal = 0
		# self.location = (self.Quality, self.Signal(SignalValue=self.BestSignal), Colour, -1)	# -1 == negative size --> relative size instead of pixel
		self.location = (self.Quality, self.Signal(), self.color, -1)	# -1 == negative size --> relative size instead of pixel

	def Signal(self, SignalValue=None):
		"""	returns the signal displayed based on a quantized version of the feature 
		"""
		def quantization(signal):
			"""	returns a quantized value of signal 
		"""
			Levels = Gbl['Levels']
			if Levels == []:
				# ====== Making signals discrete to avoid absurd precision
				Levels = list(range(0,100, Gbl['SignalPrecision']))
			for level in Levels[::-1]:
				if signal >= level:	return level
			return signal if signal < 0 else 0			# signal may be negative in certain implementations
	
		if SignalValue is not None:
			return quantization(SignalValue)
		if self.signal is None:		# computing signal only once 
			# ====== actual investment in displays
			self.signal = quantization(self.feature('Signal'))
		return self.signal
		
	def SignallingCost(self):
		# ====== cost coefficient decreases with quality
		C = ET.decrease(self.Quality, 100, Gbl['CostDecrease'])	# max =~ 0.02
		return int(Gbl['SignallingCost'] * C * self.Signal())
	
	def Policing(self):
		"""	Determines whether self is ready to exert policing (denouncing others + inflict damage)
		"""
		if Gbl['EnablePolicing']:
			if GRADUALPOLICINGPROBABILITY:
				return (random.random() < self.PolicingProbability)
			else:
				return (self.feature('PolicingProbability') >= 50)
		return False
		
	def Monitoring(self):
		"""	Determines whether self is actively monitoring other's signals
		"""
		if Gbl['EnableMonitoring']:
			return (random.random() < self.MonitoringProbability)
		return True
		
	
	def Evaluate(self, Other, OSignal=None):
		"""	self sees Other's signal and remembers it. 
			Note: OSignal may differ from Other's real signal
		"""
		assert self != Other
		SSignal = self.Signal()
		if OSignal is None:	# OSignal comes from direct observation
			OSignal = Other.Signal()
			self.ObservationMemory.add(Other)
		else:	# hearsay
			if Other in self.ObservationMemory:
				# Other is already known through their true signal
				return
			assert Gbl['Visibility'] < 100
		if (Gbl['ContemptImpact'] != 0) and (SSignal > OSignal):	# individual remembered as despicable
			self.disreputable.follow(Other, -OSignal, increasing=True)	# note the negative sign
		elif SSignal < OSignal:	# that person is admirable
			# print('.', end='', flush=True)
			self.reputable.follow(Other, OSignal, increasing=True)
		else:	# keeping the possibility of treating equality separately
			# self.pairs.follow(Other, OSignal, increasing=True)
			pass
		if Gbl['SignalAmbiguity'] and (Other in self.opaques):
			self.opaques.remove(Other)
		return

	def Observe(self, Partner):	
		"""	First round of observation. Individuals witness other's performance if visible
			and make a negative or positive opinion. They may also decide to affiliate.
		"""
		if self.activeMonitoring and (random.random() <= Gbl['Visibility'] / 100.0):
			# ====== Partner is visible to self
			self.Evaluate(Partner)
		elif Gbl['SignalAmbiguity'] and (Partner not in self.opaques):
			self.opaques.append(Partner)

	def Gossip(self, Partner):
		"""	Second round: triadic interactions. 
			Self attracts Partner's attention by talking to Partner about a third party 
		"""
		self.color = self.Colour()
		if self.activePolicing:
			# ====== self tries to find a third-party to comment upon in order to become visible to Partner
			SSignal = self.Signal()
			PSignal = Partner.Signal()

			# ====== negative GOSSIP
			# ====== self talks about worse third parties to Partner
			Other = self.disreputable.best(randomTie=True)	# = worst, actually, as negative scores stored 
			
			if (Other is None) and Gbl['SignalAmbiguity'] and (self.opaques != []):
				# ====== Policing may be directed at opaque individuals
				# This option doesn't work properly. 
				# If individuals are "opaque", Partner shouldn't be able to read their signal
				Other = random.choice(self.opaques)
				self.opaques.remove(Other)
				
			if (Other is not None) and (Other != Partner) and Gbl['ContemptImpact'] != 0:
				# ====== the point of offering someone else to criticism is to show oneself
				# OSignal = -self.disreputable.performance(Other)	# stored signal, maybe not real signal
				self.color = 'red'
				OSignal = Other.Signal()	# real signal
				assert Gbl['SignalAmbiguity'] or (OSignal < SSignal)
				# By the way: we may have OSignal >= SSignal if SignalAmbiguity
				Other.outrages += 1	# (for display)
				# if not Partner.reputable.follows(Other) and not Partner.disreputable.follows(Other):
					# print('x', end='')
				Partner.Evaluate(Other, OSignal)
				# ====== self has revealed its own signal to Partner by despising Other
				# ====== Partner just knows that SSignal > OSignal (no hypocrisy)
				# if not Partner.reputable.follows(self): print('X', end='')
				if random.random() <= (Gbl['VisibilityGossip'] / 100.0):
					Partner.Evaluate(self, SSignal)
				else:
					Partner.Evaluate(self, OSignal + 1)
					
				# ======- cost of policing at each policing act each year (here) vs. each year
				# self.Points += Gbl['PolicingCost']
				
					
			# ====== positive GOSSIP
			# ====== self talks about best third parties to Partner
			Other = self.reputable.best()
			
			if (Other is not None) and (Other != Partner) and Gbl['AdmirationImpact'] != 0:
				self.color = 'orange'
				OSignal = Other.Signal()	# real signal. Note: makes Other more visible
				assert OSignal > SSignal
				Other.praises += 1	# (for display)
				Partner.Evaluate(Other, OSignal)
				# ====== Partner just knows that SSignal < OSignal
				# Partner.Evaluate(self, OSignal - 1)
				# ====== Partner just knows that SSignal > 0
				# Partner.Evaluate(self, 1)
				# ====== Partner can see SSignal
				if random.random() <= (Gbl['VisibilityGossip'] / 100.0):
					Partner.Evaluate(self, SSignal)
	
	def Interact(self, Partner):
		"""	Third round: self tries to establish friendship with Partner based on Partner's remembered signal:
			- true signal if Partner has been directly observerd
			- target's signal + 1 if Partner has gossiped about target
			- 0 otherwise
		"""
		self.Affiliate(Partner, self.ApparentSignal(Partner))	# self considers affiliating with Partner 
	
	def ApparentSignal(self, Partner):
		"""	Known Signal if Partner is known to self, otherwise 0
		"""
		if Partner in self.ObservationMemory:	
			# print('+', end='')
			return Partner.Signal()	# direct observation
		assert Gbl['Visibility'] < 100
		if Partner in self.reputable:	
			# print('+', end='')
			return self.reputable.performance(Partner)
		if Partner in self.disreputable:	
			# print('-', end='')
			return -self.disreputable.performance(Partner)
		# if Partner in self.pairs:	
			# # print('=', end='')
			# return self.pairs.performance(Partner)
		# print('o', end='')
		return 0
	
	def Affiliate(self, Partner, Performance=0):	
		"""	Asymmetrical friendship (social links)
		"""
		# ====== self selects Partner to affiliate with.
		# ====== Since 'MaxFriends' is limited, self selects Partners based on their Performance.
		return self.F_follow(0, Partner, Performance, increasing=True)
		
		
	def assessment(self):
		"""	effect of social encounters 
		"""
		# ====== Asymmetric friendship payoff
		for F in self.followees():
			# ====== individuals benefit from being followed (social links)
			F.Points += Gbl['FollowerImpact']
			if not Gbl['EnablePolicing']:
				# ====== If no praise, praising reward is converted into social reward for comparison
				F.Points += (Gbl['AdmirationImpact'] /  Gbl['MaxFriends'])
			# ====== Follower's payoff may depend on followee's quality
			# self.Points += Gbl['FollowingImpact'] * ET.increase(F.Quality/100.0, Gbl['QualityImpact'])	# linear function of quality
			self.Points += Gbl['FollowingImpact'] * ET.logistic(F.Quality)	# non-linear function of friend's quality
			
		# ====== paying the cost of signalling
		self.Points += self.SignallingCost()	# signalling cost (given as negative), paid only once

		# ====== cost of policing each year (here) vs. at each policing act
		# if self.activePolicing:
			# self.Points += Gbl['PolicingCost']
			# self.Points += (Gbl['PolicingCost'] * self.feature('PolicingProbability') / 100.0)
			# self.Points += Gbl['PolicingCost'] * self.PolicingProbability
		# ------ paying the feature, not actual policing
		self.Points += (Gbl['PolicingCost'] * self.feature('PolicingProbability') / 100.0)
		
		# ====== cost of monitoring each year (here) vs. at each monitoring act
		# self.Points += (Gbl['MonitoringCost'] * self.feature('MonitoringProbability') / 100.0)
		if Gbl['EnableMonitoring'] and self.activeMonitoring:
			self.Points += Gbl['MonitoringCost'] * self.MonitoringProbability

		# ====== effect of policing
		if self.activePolicing:
			# for G in self.reputable:	G.Points += Gbl['AdmirationImpact']
			# for W in self.disreputable:	
				# W.Points += Gbl['ContemptImpact']
				# W.outrages += 1
			best = self.reputable.best()
			worst = self.disreputable.best()
			if best is not None and Gbl['AdmirationImpact'] != 0:	
				assert best != self
				best.color = 'green3'
				best.Points += Gbl['AdmirationImpact']
				best.top = True
				# assert best.top, 'Error: best is not top'
			if worst is not None and Gbl['ContemptImpact'] != 0:	
				assert worst != self
				worst.color = 'brown'
				worst.Points += Gbl['ContemptImpact']
		# print(self.Points)
		
	def __str__(self):
		return f"{self.ID}[{self.Signal():0.1f} {int(self.Points)}]"
		
class Population(SSim.Social_Population):
	"""	defines the population of agents 
	"""
	def __init__(self, parameters, NbAgents, Observer):
		"""	creates a population of agents 
		"""
		# ====== Learnable features
		Features = dict()
		Features['Signal'] = ('blue',)	# propensity to signal one's quality
		Features['PolicingProbability'] = ('brown',)	# ability to gossip
		Features['MonitoringProbability'] = ('green', 1)	# ability to monitor signals
		# Features['Visibility'] = ('white',)	# makes signal visible
		SSim.Social_Population.__init__(self, Gbl, NbAgents, Observer, 
			IndividualClass=Individual, features=Features)

	def interactions(self, group):
		"""	interactions occur within a group 
		"""
		# ====== first round: observation (of individuals that happen to be visible)
		for Player in group:
			Player.cleanMemory()	# forget previous observations (which are obsolete due to learning)
		for Player, Partner in self.systematic_encounters(group, shuffle=False):
			Player.Observe(Partner)
		
		# ====== second round: gossip
		# print(len(group))
		# for Player in group:
			# print(len(Partner.disreputable) + len(Partner.reputable) + len(Partner.pairs), end=' ')
		# print()
		for Player, Partner in self.systematic_encounters(group, shuffle=True):
			Player.Gossip(Partner)
		
		# ====== third round: socializing: calls Interact 
		NbInteractions = Gbl['NbInteractions']
		if type(NbInteractions) == int:
			systematic = True
		else:
			systematic = False
			# ====== NbInteractions is interpreted as the fraction of the population seen by self
			NbInteractions = int(NbInteractions * self.PopSize)
		super().interactions(group, shuffle=True, systematic=systematic, NbInteractions=NbInteractions)
		# print('\n----------------------------------------------')

		
		# for Player, Partner in list(self.encounters(group, systematic=True, shuffle=False)):
			# ====== giving a chance for isolated individuals to affiliate to someone
			# Player.Affiliate(Partner)
		# print([indiv.nbFollowers() for indiv in group if indiv.nbFollowers() != Gbl['MaxFollowers']])
		
	def display(self):
		super().display()	# displays curves, field and social links - calls agent.update
		# ====== 'Trajectories' window
		if self.Obs.Visible():	# Statistics for display
			self.Obs.record((100,100, 0, 0), Window='Trajectories')	# sets the frame
			for A in self:
				Colour = A.Colour()
				# TrPosition = (A.Signal()+10*random.random(), A.outrages, Colour, 7)
				# TrPosition = (A.Signal()+10*random.random(), 98 * A.PolicingProbability, Colour, -1)
				# TrPosition = (A.Signal() + 6*random.random(), A.feature('PolicingProbability'), Colour, -1)
				# TrPosition = (1000+A.Points, A.Signal(), Colour, 12)
				TrPosition = (A.Quality, A.feature('PolicingProbability'), 'orange', -1)
				self.Obs.record((A.ID, TrPosition), Window='Trajectories')

	def display_curves(self):

		self.Obs.curve('SignalLevel', self.SignalAvg(), Color='blue', Thickness=2, Legend='Signal')

		if Gbl['EnablePolicing']:
			self.Obs.curve('PolicingProbability', self.PolicingAvg(), Color='orange', Thickness=3, Legend='Policing Probability')

		if Gbl['EnableMonitoring']:
			self.display_feature('MonitoringProbability')

		TopSignallers, Legend = self.TopSignal()
		self.Obs.curve('TopSignallers', TopSignallers, Color='green', Thickness=3, Legend=Legend)
			

	def SignalAvg(self):
		"""	average signal in the population
		"""
		Avg = 0
		for I in self:	Avg += I.Signal()
		if self.Pop:	Avg /= len(self.Pop)
		return Avg

	def TopSignal(self):
		"""	Computes average signal of top signallers
		"""
		Percentile = 5
		# ====== using club as a limited list
		TopSignallers = EA.club(sizeMax=int(self.PopSize * Percentile / 100.0))	
		for I in self:	
			if I.Age < Gbl['MemorySpan']:	continue
			# TopSignallers.select(I, I.Signal())	# only enters if signal is large enough
			TopSignallers.select(I, I.BestSignal)	# only enters if signal is large enough
		assert len(TopSignallers) > 0
		return TopSignallers.average(), f'Avg signal of {Percentile}% top signalers'
		"""
		TSProp = 0	# number of top signalers

		if Gbl['AdmirationImpact'] != 0 and Gbl['Levels'] == []:	# continuous praise
			TSSignal = 0	# signal of top signalers
			for I in self:	
				if I.top:
					TSProp += 1
					TSSignal += I.Signal()	# avg signal of top signalers
			Legend = 'Avg signal of top signalers'
			return TSSignal / TSProp if TSProp else 0, Legend
		for I in self:	
			TSProp += (1 if I.Signal() >= I.Signal(90) else 0)	# number of top signalers
		TopSignallersMultFactor = 10 if Gbl['AdmirationImpact'] != 0 else 1
		Legend = 'Proportion of top signalers' + f" x {TopSignallersMultFactor}" * (TopSignallersMultFactor != 1)
		return TSProp / len(self.Pop) if self.Pop else 0, Legend
		"""
		
	def PolicingAvg(self):
		"""	average policing probability in the population
		"""
		Avg = 0
		for I in self:	Avg += 100 * I.PolicingProbability
		if self.Pop:	Avg /= len(self.Pop)
		return Avg


	def Dump(self, Slot):
		""" Saving investment in signalling for each adult agent
			and then distance to best friend for each adult agent having a best friend
		"""
		if Slot == 'DistanceToBestFriend':
			D = [(agent.Quality, "%d" % abs(agent.best_friend().Quality - agent.Quality)) for agent in self if agent.adult() and (agent.best_friend() is not None)]
			D += [(agent.Quality, " ") for agent in self if agent.best_friend() == None or not agent.adult()]
		else:
			D = [(agent.Quality, "%2.03f" % agent.feature(Slot)) for agent in self]
		return [Slot] + [d[1] for d in sorted(D, key=lambda x: x[0])]
		# return D
		

if __name__ == "__main__":
	Gbl = SSim.Global('___Patriot.evo')
	B = Gbl['LevelBase']	# not evenly spaced levels if B is nonzero (or mere tuple of levels)
	Gbl['Levels'] = []
	if type(Gbl['SignalLevels']) == int:
		if B > 0:	
			Gbl['Levels'] = [(B**level-1) * 100/B**Gbl['SignalLevels'] 
					for level in range(1, Gbl['SignalLevels']+1)]
		elif B < 0:
			Gbl['Levels'] = sorted([90 - abs(B)**level * 90/B**Gbl['SignalLevels'] 
					for level in range(1, Gbl['SignalLevels']+1)])
		else:	Gbl['Levels'] = [level * 90/Gbl['SignalLevels'] 
					for level in range(1, Gbl['SignalLevels']+1)]
	else:	# levels directly provided as tuple
		Gbl['Levels'] = tuple(Gbl['SignalLevels'])
		# Gbl['SignalLevels'] = len(Gbl['Levels'])
	if Gbl['BatchMode'] == 0:	
		print(__doc__)
		print('Levels:', list(map(int, Gbl['Levels'])))
	# Start()
	SSim.Start(Params=Gbl, PopClass=Population, ObsClass=Observer, DumpFeatures=['Signal', 'PolicingProbability'], Windows='FCNT')


__author__ = 'Dessalles'

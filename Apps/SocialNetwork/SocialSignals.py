#!/usr/bin/env python3

""" @brief  Study of the role of signalling in the emergence of social networks:
Individuals must find a compromise between efforts devoted to signalling
and the probability of attracting followers.
Links are supposed to be symmetrical.
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
sys.path.append('../../..')

from Evolife.Tools import Tools
from Evolife.Social import SocialSimulation

SocialValue = None	# utility class - will be a global object
Gbl = None	# will hold global parameters

class Observer(SocialSimulation.Social_Observer):
	def Field_grid(self):
		"""	initial draw: here a blue line 
		"""
		return [(0, 0, 'blue', 1, 100, 100, 'blue', 1), (100, 100, 1, 0)]
		
class SocialValues:
	"""	A few functions used to rule interactions between agents 
	"""
	def __init__(self, RankEffect, SocialOverlap, MaxFriends):
		self.RkEffect = RankEffect/100.0
		self.Overlap = SocialOverlap
		self.MaxFriends = MaxFriends
		self.RankEffects = []   # table of decreasing investments in friendship
		self.RankEffect(0)
	
	def RankEffect(self, Rank):
		""" computes a decreasing coefficient depending on one's rank
			in another agent's address book.
		"""
		if self.RankEffects == []:
			# Initializing the table of social time given to friend
			# depending on friend's rank

			#	-----------------------------------------------------------
			#   T: total amount of available time
			#   tn: social time devoted to nth friend
			#   Tn: occupied social time with n friends
			#   T1 = t1
			#   Tn = Tn-1 + tn * (1 - Tn-1 / T)
			#   Tn = Tn-1 (1 - tn / T) + tn
			# T controls overlap:
			# T= 1 ==> all social time is crowded within constant time
			#	   much overlap, more friends does not decrease
			#	   each friend's share significantly
			# T= 100  ==> no overlap, social times add to each other,
			#	   shares diminish as the number of friends increases
			#	-----------------------------------------------------------
			
			self.RkEffect = Gbl.Param('RankEffect')/100.0
			if self.RkEffect == 0:
				self.RkEffect = 0.000001
			if self.Overlap:	T = 100 * self.RkEffect / self.Overlap
			else:	T = 10000.0
			for n in range(self.MaxFriends + 2):
				tn = (self.RkEffect) ** (n+1)	# friend #0 gets time = RkEffect; friend #1 gets time = RkEffect**2;
				if n == 0:	Tn = self.RkEffect
				else:	Tn = self.RankEffects[n-1][0] * (1-tn/T)  + tn
				self.RankEffects.append((Tn,tn))
				
		if Rank >= 0:
			try:	return self.RankEffects[Rank]
			except IndexError:
				Tools.error('S_Signalling: RankEffect', str('Rank == %d' % Rank))
		else:	return (0,0)

	def SocialOffer(self, Competence, PartnerRank, nbFriends):	   
		""" An agent's social offer depends on its alleged competence (=signal) or real competence (=quality),
			on the rank it offers in its address book, and on the number of friends already
			present in the address book (as it may influence available time)
		"""
		if PartnerRank < 0:	return 0
		rankEffect = self.RankEffect(PartnerRank)[1]	# rank in address book matters
		sizeEffect = self.RankEffect(1 + nbFriends)[0]	# size of address book matters
		return float(Competence * rankEffect) / sizeEffect

	
class Individual(SocialSimulation.Social_Individual):
	"""	class Individual: defines what an individual consists of 
	"""
	def __init__(self, IdNb, maxQuality=100, features=None, parameters=None):
		# Learnable features
		self.SignalLevel = 0
		self.MinFriendSignalLevel = 100
		self.BestSignal = 0	# best signal value in memory
		SocialSimulation.Social_Individual.__init__(self, IdNb, features=features, maxQuality=maxQuality, parameters=Gbl)

	def Reset(self, Newborn=True):		# called by Learner when born again
		SocialSimulation.Social_Individual.Reset(self, Newborn=Newborn)
		self.Points = 0	# redundant
		self.Risk = 0

	def update(self, infancy=True):
		Colour = 'brown'
		if infancy and not self.adult():	Colour = 'pink'
		# self.SignalLevel = Tools.percent(self.Features['SignalInvestment'] * self.Quality)
		self.SignalLevel = Tools.noise_mult(self.Signal(), Gbl.Param('PerceptionNoise'))					
		BR = self.bestRecord()
		if BR:	self.BestSignal = BR[0]['SignalInvestment'] * self.Quality / 100.0
		else:	self.BestSignal = 0
		# self.location = (self.ID, self.Features['SignalInvestment'], Colour)
		self.location = (self.Quality, self.BestSignal+1, Colour, -1)	# -1 == negative size --> logical size instead of pixel
		if Gbl.Param('Links') and self.best_friend():
			self.location += (self.best_friend().Quality, self.best_friend().BestSignal+1, 21, 1)

	def Signal(self, Feature=None):
		"""	returns the actual quality of an individual or its displayed version 
		"""
		if Gbl.Param('Transparency'):	return self.Quality
		BC = Gbl.Param('BottomCompetence')
		Comp = Tools.percent(100-BC) * self.Quality + BC
		VisibleCompetence = Tools.percent(Comp * self.feature(Feature))	   
		return  self.Limitate(VisibleCompetence, 0, 100)
		
	def Interact(self, Partner):	self.groom(Partner)

	#------------------------------------------------------------------------------------
	# NegotiateOffer --> Offer --> SocialOffer     <-- assessment (with true competence)
	#------------------------------------------------------------------------------------
	
	def NegotiateOffer(self, Partner):
		""" returns the ranks Agent and Partner are ready to assign to each other
			in their respective address book. Agent's rank recursively depends on
			Partner's attitude towards Agent.
		"""
		# non-recursive version
		MaxOffer = 100
		OldAgentOffer = OldPartnerOffer = (0,0) # (Rank, Offer)
		AgentOffer = PartnerOffer = (0, MaxOffer)	# AgentOffer = Agent's offer to Partner
		while (OldAgentOffer, OldPartnerOffer) != (AgentOffer,PartnerOffer):
			(OldAgentOffer, OldPartnerOffer) = (AgentOffer, PartnerOffer)
			PartnerOffer = Partner.Offer(AgentOffer)
			if PartnerOffer[0] < 0: return (0,0)
			AgentOffer = self.Offer(PartnerOffer)
			#print 'Negotiation2: %s offers %d and %s offers %d (at ranks %d, %d)' \
			#	 % (self.ID,AgentOffer[1],Partner.ID,PartnerOffer[1],AgentOffer[0], PartnerOffer[0])
			if AgentOffer[0] < 0:	return (0,0)
		# print(AgentOffer[0], PartnerOffer[0])
		return (AgentOffer[1], PartnerOffer[1])			

	def Offer(self, PartnerOffer, Feature=None):
		""" Agent is going to make an offer to Partner, based on Partner's offer
		"""
		global SocialValue	# utility functions
		(PartnerRankOffer, PartnerSocialOffer) = PartnerOffer
		OfferedRank = self.accepts(PartnerSocialOffer)
		# # # if Gbl.Param('SocialSymmetry') > 0 and OfferedRank >= 0:
			# # # # Social symmetry supposes that friends put themselves at identical levels in their address book
			# # # OfferedRank = max(PartnerRankOffer, OfferedRank) # worst of the two ranks
		Signal = self.Signal(Feature=Feature)
		if Gbl.Param('Transitivity'):	Signal = min(Signal, self.MinFriendSignalLevel)	# I am not better than my friends
		SocialOffer = SocialValue.SocialOffer(Signal, OfferedRank, self.nbFriends())
		#print(self.ID, self.SignalLevel, OfferedRank, SocialOffer)
		return (OfferedRank, SocialOffer)
		
	def groom(self, Partner):
		""" The two individuals negotiate partnership.
			First they signal their competence.
			Then, they make a "social offer" based on the rank
			(in their "address book") they are ready to assign to each other.
			Lastly, each one independently decides to join the other or not.
			cf. Dunbar's "grooming hypothesis"
		"""

		# new interaction puts previous ones into question
		if self.follows(Partner):	self.end_friendship(Partner)	# symmetrical splitting up

		# Negotiation takes place
		(IndivOffer, PartnerOffer) =  self.NegotiateOffer(Partner)

		# social links are established accordingly
		if IndivOffer == 0 or PartnerOffer == 0:
			# One doesn't care about the other
##            print "\nNo deal: %s(%d)->%d, %s(%d)->%d" % \
##                (self.ID, self.SignalLevel, IndivOffer, Partner.ID, Partner.SignalLevel, PartnerOffer)
			return # the deal is not made

		if not self.get_friend(IndivOffer, Partner, PartnerOffer):
			print("***** Scenario Signalling: Negotiation not respected")
			print(self.ID, 'was accepted by', Partner.ID)
			print('with offer-:', IndivOffer)
			print(self.ID, sorted(self.friends.performances()))
			# print sorted(self.followers.performances())
			print(Partner.ID, sorted(Partner.friends.performances()))
			# print sorted(Partner.followers.performances())
			Tools.error('S_Signalling', "Negotiation not respected")
			return # the deal is not made
		elif self.MinFriendSignalLevel > Partner.Signal():	
			self.MinFriendSignalLevel = Partner.Signal()
		return
		
	def Cost(self, Feature=None):
		return Tools.percent(Gbl.Param('SignallingCost') * self.feature(Feature))
	
	def assessment(self):
		"""	computing social payoff - called by Learner 
		"""
		global SocialValue	# utility functions
		# first, pay the cost for signalling
		self.Points -= self.Cost()
		# self.restore_symmetry() # Checks that self is its friends' friend
		# being acquainted provides benefit to friend
		for (Rank, Friend) in enumerate(self.followees()):
			# computing real friendship effect 
			AgentSocialEffect = SocialValue.SocialOffer(self.Quality, Rank, self.nbFriends())
			Friend.Risk = Tools.percent(Friend.Risk * (100 - Tools.percent(Gbl.Param('CompetenceImpact')
																	   * AgentSocialEffect)))
				
	def wins(self, Points):
		"""	stores a benefit	
		"""
		self.Points += 100 - self.Risk
		# self.Points = Gbl.InterActions.Saturate(self.Points)
		SocialSimulation.Social_Individual.wins(self, self.Points)
	
	def __str__(self):
		return "%s[%0.1f]" % (self.ID, self.SignalLevel)
		
class Population(SocialSimulation.Social_Population):
	"""	defines the population of agents 
	"""
	def __init__(self, parameters, NbAgents, Observer, IndividualClass=None, features={}):
		if not features:
			features = {'SignalInvestment':('blue',)}   # propensity to signal one's quality
		"""	creates a population of agents 
		"""
		SocialSimulation.Social_Population.__init__(self, Gbl, NbAgents, Observer, 
				IndividualClass=Individual, features=features)
		

	def season_initialization(self):
		for agent in self.Pop:
			# agent.lessening_friendship()	# eroding past gurus performances
			if self.Param('EraseNetwork'):	agent.forgetAll()
			agent.Points = 0
			agent.Risk = 100	# maximum risk
		
			
				
	def Dump(self, Slot):
		""" Saving investment in signalling for each adult agent
			and then distance to best friend for each adult agent having a best friend
		"""
		if Slot == 'DistanceToBestFriend':
			D = [(agent.Quality, "%d" % abs(agent.best_friend().Quality - agent.Quality)) for agent in self.Pop if agent.adult() and agent.best_friend() is not None]
			D += [(agent.Quality, " ") for agent in self.Pop if agent.best_friend() == None or not agent.adult()]
		else:
			D = [(agent.Quality, "%2.03f" % agent.Features[Slot]) for agent in self.Pop]
		return [Slot] + [d[1] for d in sorted(D, key=lambda x: x[0])]
		
def Start(Params=None):
	global Gbl, SocialValue
	if Params is not None: 	Gbl = Params
	# utility functions
	SocialValue = SocialValues(Gbl.Param('RankEffect'), Gbl.Param('SocialOverlap'), Gbl.Param('MaxFriends'))
	
	


if __name__ == "__main__":
	Gbl = SocialSimulation.Global()
	if Gbl['BatchMode'] == 0:	print(__doc__)
	Start()
	SocialSimulation.Start(Params=Gbl, PopClass=Population, ObsClass=Observer)


__author__ = 'Dessalles'

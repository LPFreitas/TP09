#!/usr/bin/env python3

""" @brief 	Individuals inherit this class which determines who is friend with whom.

	Useful classes are:
	- Liker: individuals bookmark other individuals based on their performance
	- Friend: Liker + possibility of imposing symmetrical liking links
	- Follower: idem + the liked individuals know who likes them
	- Friendship: Follower + possibility of imposing symmetrical liking links
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
#  Alliances                                                                 #
##############################################################################


import sys
import random

if __name__ == '__main__':  sys.path.append('../..')  # for tests


from Evolife.Tools.Tools import error

CHECKCONSISTENCY = False

class club:
	""" List of individuals associated with their performance.
		The performance is used to decide who gets acquainted with whom.
	"""

	def __init__(self, sizeMax = 0):
		"""	initializes club as an empty list of couples (individual,performance)
		"""
		self.sizeMax = sizeMax
		if sizeMax == 0:	self.sizeMax = sys.maxsize
		self.reset()

	def reset(self):
		self.__members = []   # list of couples (individual,performance)
		
	def names(self):	
		"""	returns members' names (first elements of couples stored in members)
		"""
		return [T[0] for T in self]

	def performances(self):	
		"""	returns members' performances (second elements of couples stored in members)
		"""
		return [T[1] for T in self]
		
	def present(self, MemberPerf):	
		"""	returns True if the couple MemberPerf belongs to the club
		"""
		return MemberPerf in self.__members
			
	def ordered(self, reverse=True):
		"""	returns a list of members names  (ordered by decreasing performance by default)
		"""
		return [T[0] for T in sorted(self.__members, key = lambda x: x[1], reverse=reverse)]
		
	def rank(self, Member):
		"""	returns the rank of Member in the list of decreasing performances
		"""
		try:	return self.ordered().index(Member)
		except ValueError:	return -1

	def performance(self, Member):
		"""	returns the performance of Member
		"""
		try:	return self.__members[self.names().index(Member)][1]
		except ValueError:	error('Alliances', 'Searching for non-member')
	
	def size(self):	
		"""	size of the club
		"""
		return len(self)

	def minimal(self):
		"""	returns the minimal performance among members
		"""
		if len(self):	return min([T[1] for T in self])
		return -1

	def maximal(self):
		"""	returns the maximal performance among members
		"""
		if len(self):	return max([T[1] for T in self])
		return -1

	def best(self, randomTie=False):
		"""	returns the member with the best performance
		"""
		if len(self):	
			if randomTie:
				bestPerformance = self.maximal()
				return random.choice([T[0] for T in self if T[1] == bestPerformance])
			else:	return max(self, key=lambda x: x[1])[0]
		return None

	def worst(self):
		"""	returns the member with the worst performance 
		"""
		if len(self):	
			return min(self, key=lambda x: x[1])[0]
			# return self.ordered(reverse=False)[0]
		return None

	def average(self):
		"""	returns average performance 
		"""
		if len(self):	
			return sum([m[1] for m in self]) / len(self)
		return None

	def accepts(self, performance, conservative=True):
		""" Checks whether an individual with 'performance' can be accepted into the club 
			Always true if club is not full.
			Returns admission rank.
		"""
		if len(self) >= self.sizeMax:
			if conservative and performance <= self.minimal():
				return -1   # equality: priority given to former members
			elif performance < self.minimal():	return -1
		# ------ returning the rank that the candidate would be assigned
		rank = len(self) - sorted([performance] + self.performances()).index(performance)
		assert rank <= self.sizeMax, f"rank = {rank} exceeds max size = {self.sizeMax} (actual size is {len(self)})"
		return rank
		
	def enters(self, newMember, performance, conservative=True, check =True):
		"""	If newMember is accepted based on its performance, it enters the club.
			If too many members in the club, the worst one is ejected and returned
		"""
		if self.accepts(performance, conservative=conservative) >= 0:
			# ------ First, check whether newMember is not already a member
			if newMember in self.names():
				self.exits(newMember)   # to prepare the come-back
			if self.size() >= self.sizeMax:
				worst = self.worst() # the redundant individual will be ejected
			else:	worst = None
			self.__members.append((newMember, performance))
			return worst
		if check:	error("Alliances: unchecked admittance")
		return None

	def select(self, newMember, performance):
		"""	same as "enters", but performs selection to limit size
		"""
		worst = self.enters(newMember, performance, check=False)
		if worst is not None:	# worst individual is displaced
			self.exits(worst)

	def exits(self, oldMember):
		"""	a member goes out from the club 
		"""
		for (M,Perf) in self.__members[:]:  # safe to copy the list as it is changed within the loop
			if M == oldMember:
				self.__members.remove((oldMember,Perf))
				return True
		print('exiled: %s' % str(oldMember))
		error('Alliances: non-member attempting to quit a club')
		return False

	def weakening(self, Factor = 0.9):  # temporary value
		"""	all performances are reduced (represents temporal erosion) 
		"""
		for (M,Perf) in self.__members[:]:  # safe to copy the list as it is changed within the loop
			self.__members.remove((M, Perf))
			self.__members.append((M, Perf * Factor))

	def limit(self, NumberOfMembers):
		"""	keeps only a limited number of members
		"""
		self.__members.sort(key = lambda x: x[1], reverse=True)
		self.__members = self.__members[:NumberOfMembers]
		
	def __iter__(self):	return iter(self.__members)
	
	def __len__(self): return len(self.__members)
	
	def __contains__(self, T): return (T in self.names())
		
	def __str__(self):
		# return "[" + '-'.join([T.ID for T in self.ordered()]) + "]"
		return "[" + '-'.join([str(T) for T in self.names()]) + "]"

	def consistency(self):
		if self.size() > 0:
			if not self.present((self.best(), self.maximal())):
				print(self.best())
				print(self.maximal())
				print(self)
				error("Alliances: best is ghost")
	
class Liker:
	"""	A liker keeps a list of other individuals in memory based on their performances
	"""
	
	def __init__(self, MaxFriends=1):
		"""	Defines Friend as a club
		"""
		self.friends = club(MaxFriends)
	
	#################################
	# asymmetrical links            #
	#################################
	def accepts(self, F_perf):	
		""" Checks whether an individual with 'performance' can be accepted as a friend.
			Returns admission rank
		"""
		return	self.friends.accepts(F_perf)
	
	def affiliable(self, F_perf, conservative=True):
		"""	Checks whether affiliation is possible 
		"""
		return	self.friends.accepts(F_perf, conservative=conservative) >= 0

	def follow(self, F, F_perf, conservative=True, Quit=None, increasing=False):
		""" the individual wants to be F's disciple due to F's performance
		"""
		# print self.ID, "wants to follows", (F.ID, F_perf)
		if increasing and self.follows(F) and F_perf <= self.performance(F):
			# ------ In the increasing condition, friends are kept if already present with higher performance
			return True
		if self.affiliable(F_perf, conservative=conservative):
			# the new friend is good enough
			RF = self.friends.enters(F, F_perf, conservative=conservative)	# returns ejected old friend
			if RF is not None:
				# print('redundant friend of %s: %s' % (self, RF))
				# print('self: %s' % self, ">>> self's friends: %s " % map(str, Friend.social_signature(self)))
				if Quit is None: Quit = self.quit_
				Quit(RF)   # some redundant friend is disowned
			return True
		else:	return False
			
	def follows(self, Friend):	
		"""	checks whether Friend belongs to actual friends
		"""
		return Friend in self.names()
		# R = Friend in self.friends.names()
		# if R: print self.ID, 'is already following', Friend.ID
	
	def quit_(self, Friend=None):
		""" the individual no longer follows its friend
		"""
		if Friend is None: Friend = self.friends.worst()
		if Friend is not None:
			# print(self, 'quits ', Friend)
			self.friends.exits(Friend)
	
	def best(self, randomTie=False):	return self.friends.best(randomTie=randomTie)
	
	def performance(self, Friend):
		"""	returns Friend's stored performance
		"""
		return self.friends.performance(Friend)
	
	def Max(self):	return max(0, self.friends.maximal())
	
	def followees(self, ordered=True):	
		"""	returns a list of liked names  (ordered by decreasing performance by default)
		"""
		if ordered:	return self.friends.ordered()
		return self.names()

	def names(self):	
		"""	returns the list of friends' names
		"""
		return self.friends.names()
	
	def rank(self, Friend):	
		"""	returns the rank of Friend in the list of decreasing performances
		"""
		return self.friends.rank(Friend)
	
	def nbFriends(self):	
		"""	Number of friends
		"""
		return self.friends.size()
		
	def size(self):
		"""	Number of friends
		"""	
		return self.friends.size()
		
	def sizeMax(self):		return self.friends.sizeMax

	def lessening_friendship(self, Factor=0.9):
		"""	all performances are reduced (represents temporal erosion) 
		"""
		self.friends.weakening(Factor)					

	def limit(self, NumberOfFriends):
		return self.friends.limit(NumberOfFriends)
	
	def checkNetwork(self, membershipFunction=None):
		"""	updates links by forgetting friends that are gone 
		"""
		for F in self:
			if not membershipFunction(F):	self.quit_(F)
		
	def detach(self):
		""" The individual quits all its friends	
		"""
		# for F in self:	self.quit_(F)
		self.friends.reset()
		
	def __iter__(self):	return iter(self.friends.names())
	
	def __len__(self): return len(self.friends)
		
	def social_signature(self):
		"""	returns the ordered list of friends
		"""
		# return [F.ID for F in self.friends.names()]
		return self.followees()

	def signature(self):	
		"""	same as social_signature
		"""
		return self.social_signature()

	def __contains__(self, T): return (T in self.friends)
	
	def __str__(self):
		return str(self.friends)

class Friend(Liker):
	"""	defines symmetrical  acquaintances
		self	<--->  Partner
	"""
	def acquaintable(self, Offer, Partner, PartnerOffer):
		"""	Checks that self and Partner would accept each other as friend, based on their performance
		"""
		return self.affiliable(PartnerOffer) and Partner.affiliable(Offer)
	
	def get_friend(self, Offer, Partner, PartnerOffer):
		"""	Checks mutual acceptance and then establishes friendship 
		"""
		if self.acquaintable(Offer, Partner, PartnerOffer):
			if not self.follow(Partner, PartnerOffer, Quit=self.end_friendship):
				error("Friend: self changed mind")
			if not Partner.follow(self, Offer, Quit=Partner.end_friendship):
				error("Friend: Partner changed mind")
			return True
		return False
		
	def acquainted(self, Partner):
		"""	same as get_friend/3 with no performance 
		"""
		return self.get_friend(0, Partner, 0)
		
	def end_friendship(self, Partner):
		"""	Partners remove each other from their address book 
		"""
		# print('\nsplitting up', self.ID, Partner.ID)
		self.quit_(Partner)
		Partner.quit_(self)

	def forgetAll(self):
		""" The individual quits its friends	
		"""
		for F in self:	self.end_friendship(F)

class Follower(Liker):
	""" Augmented version of Liker
		'Follower' in addition knows about who is following self
		
		self	--->  Guru	(as liker)
		Guru	--->  self	(as follower)
	"""
	
	def __init__(self, MaxGurus, MaxFollowers=0):
		"""	calls the Liker constructor for followees.
			creates another Liker object for followers
		"""
		Liker.__init__(self, MaxGurus)
		if MaxFollowers:
			self.followers = Liker(MaxFollowers)	# 'Liker' used as a mirror class to keep track of followers
		else:	self.followers = None
	
	def F_affiliable(self, perf, guru, G_perf, conservative=True):
		""" Checks whether affiliation is possible
			by checking acceptance both in friends and in followers
		"""
		A = self.affiliable(G_perf, conservative=conservative)	# guru is acceptable and ...
		if self.followers is not None:	
			A &= guru.followers.affiliable(perf, conservative=conservative)	# ...self acceptable to guru
		return A
	
	def F_follow(self, perf, G, G_perf, conservative=True, increasing=False):
		""" the individual wants to be G's disciple because of some of G's performance
			G may evaluate the individual's performance too
		"""
		if self.F_affiliable(perf, G, G_perf, conservative=conservative):
			# ------ the new guru is good enough and the individual is good enough for the guru
			# print('%s (%s) is about to follow %s (%s)' % (self, list(map(str, self.social_signature())), G, list(map(str, G.social_signature()))))
			if not self.follow(G, G_perf, conservative=conservative, Quit=self.G_quit_, increasing=increasing):
				error("Alliances", "inconsistent guru")
			if G.followers is not None:	
				if not G.followers.follow(self, perf, conservative=conservative, Quit=G.F_quit_, increasing=increasing):
					error('Alliances', "inconsistent self")
			if CHECKCONSISTENCY:	self.consistency(); G.consistency()
			return True
		else:	return False

	def G_quit_(self, guru):
		""" the individual no longer follows its guru
		"""
		self.quit_(guru)
		# if guru.followers is not None: 	guru.followers.quit_(self)
		guru.followers.quit_(self)

	def F_quit_(self, follower):
		""" the individual does not want its disciple any longer
		"""
		assert self.followers is not None, "Alliances: No Follower whatsoever"
		self.followers.quit_(follower)
		follower.quit_(self)

	def nbFollowers(self):	return self.followers.nbFriends()

	def limit(self, NumberOfFriends):
		# Warning: untested
		for Guru in self.ordered()[:NumberOfFriends]:
			self.G_quit_(Guru)
		
	def limit_followers(self, NumberOfFollowers):
		# Warning: untested
		for follower in self.followers.ordered()[:NumberOfFollowers]:
			self.F_quit_(follower)
	
	def follower_rank(self, Friend):
		"""	Returns Friend's rank among self's followers
		"""
		if self.followers:	return self.followers.rank(Friend)
		return -1
	
	def is_follower(self, Friend):
		"""	Checks that Friend is among self's followers
		"""
		if self.followers:	return Friend in self.followers
		return False

	def is_followee(self, Friend):
		"""	Checks that Friend is followed by self
		"""
		return Friend in self
		
	def forgetAll(self):
		"""	calls 'detach' for self's followers and then for self.
		"""
		if self.followers is None:	Friend.forgetAll(self)
		else:	self.detach()

	def detach(self):
		""" The individual quits its guru and quits its followers
		"""
		for G in self.names():		self.G_quit_(G)	# G is erased from self's guru list
		if self.names() != []:		error("Alliances: recalcitrant guru")
		if self.followers is not None:
			for F in self.followers.names():	self.F_quit_(F)	# self is erased from F's guru list
			if self.followers.names() != []:	error("Alliances: sticky  followers")
	
	
	def consistency(self):
		"""	checks social links consistency (self belongs to the followers of its followees)
		"""
		for F in self.followers:
			if self not in F:
				print('self: %s' % self)
				print("self's followers: %s" % list(map(str, self.followers.names())))
				print('follower: %s' % F)
				print('its gurus: %s' % list(map(str, F.friends.names())))
				error("Alliances: non following followers")
			if self == F:	error("Alliances: Narcissism")
##            print self.ID, ' is in ', F.ID, "'s guru list: ", [G.ID for G in F.gurus.names()]
		for G in self:
			if self not in G.followers:
				print('\n\nself: %s' % self)
				print("self's gurus: %s" % list(map(str, self.friends.names())))
				print('guru: %s' % G)
				print('its followers: %s' % list(map(str, G.followers.names())))
				error("Alliances: 	 guru")
			if self == G:	error("Alliances: narcissism")
##            print self.ID, ' is in ', G.ID, "'s follower list: ", [F.ID for F in G.followers.names()]
##        print '\t', self.ID, ' OK'
		self.friends.consistency()
		return ('%s consistent' % self.ID)
	
class Friendship(Follower):
	""" Augmented version of Follower for symmetrical links.
		
		self	<--->  friend  (with bidirectional access)
	"""
	def acquaintable(self, Offer, Partner, PartnerOffer):
		"""	Checks that self and Partner would accept each other as friend, based on their performance
		"""
		return self.affiliable(PartnerOffer) and Partner.affiliable(Offer)

	def get_friend(self, Offer, Partner, PartnerOffer):
		"""	Checks mutual acceptance and then establishes friendship 
		"""
		if self.acquaintable(Offer, Partner, PartnerOffer):
			if not self.F_follow(Offer, Partner, PartnerOffer):
				error("Friend: self changed mind")
			if not Partner.F_follow(PartnerOffer, self, Offer):
				error("Friend: Partner changed mind")
			return True
		return False

	def end_friendship(self, Partner):
		"""	Partners remove each other from their address book 
		"""
		# print('\nsplitting up', self.ID, Partner.ID)
		# print(self.consistency(), Partner.consistency())		
		if CHECKCONSISTENCY:	self.consistency(); Partner.consistency()
		self.G_quit_(Partner)
		Partner.G_quit_(self)

	def best_friend(self, randomTie=False):	return self.best(randomTie=randomTie)



###############################
# Local Test                  #
###############################

if __name__ == "__main__":
	print(__doc__ + '\n')
	print(Friend.__doc__ + '\n\n')
	raw_input('[Return]')


__author__ = 'Dessalles'

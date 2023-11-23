#!/usr/bin/env python3

""" @brief  Social Bubble formation due to recommender systems:
The point is to show that isolated communities emerge due to recommendation
based on resemblance
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
# Social Bubble formation due to recommender systems                         #
##############################################################################

import sys
sys.path.append('..')
sys.path.append('../../..')

import random
from math import copysign

import Evolife.Ecology.Observer				as EO
import Evolife.Scenarii.Parameters 			as EPar
import Evolife.Graphics.Evolife_Window 	as EW
import Evolife.Graphics.Landscape			as Landscape

INDIV_ASPECT = ('red', -1)	# negative size makes it zoomable
FILM_ASPECT = ('green', -2)	# negative size makes it zoomable
ERASE_ASPECT = (1,1,-1,)	# negative colour erases from display


class Scenario(EPar.Parameters):
	def __init__(self):
		# Parameter values
		EPar.Parameters.__init__(self, CfgFile='_Params.evo')	# loads parameters from configuration file
		#############################
		# Global variables		    #
		#############################

		
class Individual:
	""" Defines individual agents
	"""
	def __init__(self, ID, Type='individual', Aspect=INDIV_ASPECT):
		# print 'creating', self.ID
		self.ID = ID
		self.Aspect = Aspect
		self.Type = Type
		def randomLoc():	
			return (random.randint(0, Gbl['LandSize']-1),
						random.randint(0, Gbl['LandSize']-1))
		self.Location = None
		while True:
			if self.move(randomLoc()):	break
		
	def display(self):
		Observer.record((self.ID, self.Location + self.Aspect)) # for ongoing display
	
	def erase(self, display=False):
		"""	erase individual from current location and possibly from display 
		"""
		if self.Location: 	Land.Modify(self.Location, None)	# delete old location
		self.Location = None
		if display:	 Observer.record((self.ID, ERASE_ASPECT))
		
	def move(self, Location):
		"""	moves agent to Location  
		"""
		if Location == self.Location:	return False
		if Land.Modify(Location, self, check=True):
			self.erase()
			self.Location = Location
			self.display()
			return True
		return False
		
	def closer(self, Location):
		"""	moves agent closer to Location 
		"""
		delta = [0,0]
		NewLoc = [0,0]
		for coord in (0,1):
			delta[coord] = (Location[coord] - self.Location[coord])
			# if abs(delta[coord]) > max(Gbl['InfluenceRadius'], Gbl['NeighbourhoodRadius']) + 1:
			# # # # if abs(delta[coord]) > Gbl['InfluenceRadius'] + Gbl['NeighbourhoodRadius'] + 1:
				# # # # # correcting for toric conversion
				# # # # delta[coord] += int(copysign(Land.Dimension[coord], -delta[coord]))
			delta[coord] =  round((delta[coord] * Gbl['Influence']) / 100.0)
			NewLoc[coord] = self.Location[coord] + delta[coord]
		# if tuple(NewLoc) == self.Location:
			# print(self, delta, Location)
		# ___OldLoc = self.Location[:]
		if self.move(Land.ToricConversion(tuple(NewLoc))):
			# print(Location, ___OldLoc, delta, self.Location)
			pass
		
	
	def inspect(self, Type, radius):
		"""	inspect neighbourhood to find items of type 'Type' (eg. films or other individuals) 
		"""
		Neighbourhood = list(Land.neighbours(self.Location, radius))
		return [Land.Content(loc) for loc in Neighbourhood 
			if Land.Content(loc) and Land.Content(loc).Type == Type]
		

	def __str__(self):	return '%s(%dx%d)' % ((self.ID,) +  self.Location)
	
class Film(Individual):
	def __init__(self, ID):
		super().__init__(ID, Type='film', Aspect=FILM_ASPECT)


class Population:
	"""	defines the set of individuals 
	"""
	def __init__(self, popSize):
		"""	creates a population of agents 
		"""
		self.popSize = popSize
		print("population size: %d" % self.popSize)
		self.members = [Individual('I%s' % str(ID).rjust(4,'0')) for ID in range(popSize)]
		self.CallsSinceLastMove = 0  # counts the number of times agents were proposed to move since last actual move
		self.films = []		# recent films
		self.currentFilm = None
			
	def selectIndividual(self):	return random.choice(self.members)
	
	def One_Decision(self):
		""" This function is repeatedly called by the simulation thread.
			One agent is randomly chosen and decides what it does
		"""
		
		Observer.season()  # sets StepId
		if self.currentFilm is None:
			# Creating film
			self.currentFilm = Film('F%d' % Observer.StepId)
			# erasing old film from display
			for film in self.films[:-Gbl['DisplayTrail']]:
				film.erase(display=True)
			return True
			
		# Influence of films on individuals
		DirectlyConcerned = self.currentFilm.inspect(Type='individual', 
			radius=Gbl['InfluenceRadius'])
		DirectlyConcerned = random.sample(DirectlyConcerned, 
			len(DirectlyConcerned) * Gbl['InfluenceRatio'] // 100)
		# Concerned = set(DirectlyConcerned)
		Concerned = DirectlyConcerned[:]	# making ground copy
		# print(len(Concerned), end=' ', flush=True)
		for indiv in DirectlyConcerned:	
			# Influence of individuals on individuals
			IndirectlyConcerned = indiv.inspect(Type='individual', radius=Gbl['NeighbourhoodRadius'])
			IndirectlyConcerned = random.sample(IndirectlyConcerned, 
				len(IndirectlyConcerned) * Gbl['InfluenceRatio'] // 100)
			# print('\t', len(IndirectlyConcerned), flush=True)
			# Concerned |= set(IndirectlyConcerned)
			Concerned += IndirectlyConcerned
		# print(len(Concerned), flush=True)
		# print(' '.join([str(D) for D in Concerned]))
		for indiv in Concerned:	indiv.closer(self.currentFilm.Location)
		# print(' '.join([str(D) for D in Concerned]))
		self.films.append(self.currentFilm)
		self.currentFilm = None
		
		

		# indiv = self.selectIndividual()	# indiv who will play the game	
		
		self.CallsSinceLastMove += 1
		if self.CallsSinceLastMove > 100 * self.popSize:
			return False	# situation is probably stable
		return True	# simulation goes on
			   


if __name__ == "__main__":
	print(__doc__)

	
	#############################
	# Global objects			#
	#############################
	Gbl = Scenario()
	# optional determinism:
	if Gbl.Parameter('RandomSeed', Default=0) > 0:	random.seed(Gbl['RandomSeed'])
	Observer = EO.Observer(Gbl)	  # Observer contains statistics
	Land = Landscape.Landscape(Gbl['LandSize'])	  # logical settlement grid
	Pop = Population(Gbl['PopulationSize'])
	
	# Observer.recordInfo('Background', 'white')
	Observer.recordInfo('FieldWallpaper', 'white')
	Observer.recordInfo('DefaultViews',	[('Field', 800, 720)])	# Evolife should start with these windows open - these sizes are in pixels
	
	
	EW.Start(Pop.One_Decision, Observer, Capabilities='RP')

	print("Bye.......")
	
__author__ = 'Dessalles'

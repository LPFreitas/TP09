#!/usr/bin/env python3

""" @brief 	Chaotic fractals
		Written by Felix Richart in 2017
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
# Chaotic fractals                                                                                           #
##############################################################################

import sys
import random
		
sys.path.append('..')
sys.path.append('../../..')
import Evolife.Scenarii.Parameters			as EPar
import Evolife.Ecology.Observer				as EO
import Evolife.Graphics.Evolife_Window	as EW
import Evolife.Tools.Tools					as ET



class Fractal:
	"""	Defines a network as a graph
	"""
	def __init__(self, Observer, Shape=[(250, 490), (10, 10), (490, 10)], Coef=0.5, InitialPos=None, DotSize=1):
		self.Observer = Observer
		self.Shape = Shape
		self.DotSize = DotSize
		self.nbOfDots = 0
		self.Coef = 1 - Coef
		self.Dot = InitialPos if InitialPos is not None else [random.randint(10, 100), random.randint(10, 100),]
		for i in range(0, len(Shape)):
			Observer.record((Shape[i][0], Shape[i][1], 'red', 8), Window='Trajectories')
		
	def addDot(self):
		"""	this function is called repeatedly by the simulation 
		"""
		self.Observer.season()
		Observer.record((self.Dot[0], self.Dot[1], 'green', self.DotSize), Window='Trajectories')
		self.nbOfDots += 1
		DotToFocus = self.Shape[random.randint(0, len(self.Shape)-1)]
		self.Dot[0] = self.Dot[0]+(DotToFocus[0]-self.Dot[0])*self.Coef
		self.Dot[1] = self.Dot[1]+(DotToFocus[1]-self.Dot[1])*self.Coef
		return True

if __name__ == "__main__":
	print(__doc__)

	#############################
	# Global objects	    #
	#############################
	Gbl = EPar.Parameters('_Params.evo')	# Loading global parameter values
	Observer = EO.Observer(Gbl)   # Observer contains statistics
	Fractal0 = Fractal(Observer, Shape=Gbl['InitialDots'], Coef=Gbl['Coefficient'], DotSize=Gbl['DotSize'])
	# Initial draw
	Observer.recordInfo('TrajectoriesWallpaper', 'yellow')
	Observer.recordInfo('TrajectoriesTitle', 'Chaotic fractals')
	Observer.recordInfo('DefaultViews', [('Trajectories', 600, 100, 800, 800)])
	# drawing an invisible diagonal to set the scale
	Observer.record((0, 0, 0, 0, 100, 100, 0, 0), Window='Trajectories')
	EW.Start(Fractal0.addDot, Observer, Capabilities='RPT', Options={'Run':True})

	print("Bye.......")

__author__ = 'Felix Richart'


#Questions : how to set depth (random or fixed)
#how to create graph (random order ?)
#fix number of hyperlinks per node or hyperlinks for the whole network
#how to plot

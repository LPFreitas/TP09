#!/usr/bin/env python3

""" @brief 	
	The Barnsley fern
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
# The Barnsley fern
# Teissier Lucas, Telecom Paris
# Imperor Lorène, Mines ParisTech
#	 - 2020
##############################################################################

#	References
#	● Wikipedia article:
#	https://en.wikipedia.org/wiki/Barnsley_fern
#	● Chaos Game - Numberphile (Youtube video):
#	https://www.youtube.com/watch?v=kbKtFN71Lfs

import sys
import random
import numpy as np

sys.path.append('..')
sys.path.append('../../..')
import Evolife.Scenarii.Parameters			as EPar
import Evolife.Ecology.Observer				as EO
import Evolife.Graphics.Evolife_Window	as EW
import Evolife.Tools.Tools					as ET


class Fougere:
	"""	Barnsley fern 
	"""

	def __init__(self, Observer, F1_coeff, F2_coeff, F3_coeff, F4_coeff, Weights, Coef=0.5, InitialPos=(5, 0), DotSize=2):
		self.Observer = Observer
		self.F1_coeff = F1_coeff
		self.F2_coeff = F2_coeff
		self.F3_coeff = F3_coeff
		self.F4_coeff = F4_coeff
		self.Weights = Weights
		self.Coef = 1 - Coef
		self.Dot = InitialPos
		self.DotSize = DotSize
		self.nbOfDots = 0
		self.vec = [5, 0]
		Observer.record((self.Dot[0], self.Dot[1], 'green', self.DotSize), Window='Trajectories')

	def addDot(self):
		"""	this function is called repeatedly by the simulation 
		"""
		self.Observer.season()
		self.Dot = self.translationInv(self.Dot)
		self.Dot = self.transform0(self.Dot)
		self.Dot = self.translation(self.Dot)
		self.DrawDot()
		self.nbOfDots += 1
		return True

	def DrawDot(self):
		Observer.record((self.Dot[0], self.Dot[1], 'green', self.DotSize), Window='Trajectories')
	
	def translation(self, dot):
		return dot[0]+self.vec[0], dot[1]+self.vec[1]

	def translationInv(self, dot):
		return dot[0]-self.vec[0], dot[1]-self.vec[1]

	def fonction_fougere(self, coeffs, old_point):
		A = np.array([[coeffs[0],coeffs[1]],[coeffs[2],coeffs[3]]])
		return np.dot(A,old_point)+ np.array([coeffs[4],coeffs[5]])

	def transform0(self, point):
		"""	Original fern transfor
		"""
		# todo : choices have weights
		choice = random.random()
		old_point = np.array(point)

		if choice < self.Weights[0]:
			return self.fonction_fougere(self.F1_coeff,old_point)
		elif choice < np.sum(self.Weights[0:2]):
			return self.fonction_fougere(self.F2_coeff,old_point)
		elif choice < np.sum(self.Weights[0:3]):
			return self.fonction_fougere(self.F3_coeff,old_point)
		else:
			return self.fonction_fougere(self.F4_coeff,old_point)


if __name__ == "__main__":
	print(__doc__)

	#############################
	# Global objects		#
	#############################
	Gbl = EPar.Parameters('_Params.evo')  # Loading global parameter values generated by starter
	Observer = EO.Observer(Gbl)  # Observer contains statistics

	InitialPos = Gbl['InitialPos']
	F1_coeff = Gbl['F1_a_b_c_d_e_f']
	F2_coeff = Gbl['F2_a_b_c_d_e_f']
	F3_coeff = Gbl['F3_a_b_c_d_e_f']
	F4_coeff = Gbl['F4_a_b_c_d_e_f']
	Weights = Gbl['Weight_p1_p2_p3_p4']
	Fougere0 = Fougere(Observer, F1_coeff=F1_coeff, F2_coeff=F2_coeff, F3_coeff=F3_coeff,
					   F4_coeff=F4_coeff, Weights=Weights, InitialPos=InitialPos,
						DotSize=Gbl['DotSize'])

	# Initial draw
	Observer.recordInfo('TrajectoriesWallpaper', 'yellow')
	Observer.recordInfo('TrajectoriesTitle', 'Barnsley fern')
	Observer.recordInfo('DefaultViews', [('Trajectories', 600, 100, 400, 400)])
	# drawing an invisible diagonal to set the scale
	Observer.record((0, 0, 0, 0, 10, 10, 0, 0), Window='Trajectories')
	EW.Start(Fougere0.addDot, Observer, Capabilities='RPT', Options={'Run':True})

	print("Bye.......")

__author__ = 'Lorène Imperor & Lucas Teissier'


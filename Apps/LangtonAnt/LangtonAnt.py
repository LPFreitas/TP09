#!/usr/bin/env python3



#============================================================================#
# EVOLIFE  http://evolife.telecom-paris.fr             Jean-Louis Dessalles  #
# Telecom Paris  2023-11-19                                www.dessalles.fr  #
# -------------------------------------------------------------------------- #
# License:  Creative Commons BY-NC-SA                                        #
#============================================================================#
# Documentation: https://evolife.telecom-paris.fr/Classes                    #
#============================================================================#


# Based on the CellularAutomaton.py program provided with EvoLife
# Developed by Ian Elmor Lang as practical work for the 2016/2017 edition of
# TPT09

import sys
sys.path.append('../../..')

import Evolife.Ecology.Observer as EO
import Evolife.Graphics.Evolife_Window as EW
import Evolife.Tools.Tools as ET
import Evolife.Scenarii.Parameters as EPar
import re

import random

ET.boost()   # A technical trick that sometimes provides impressive speeding up

class CA_Scenario(EPar.Parameters):

	def __init__(self, ConfigFile):
		EPar.Parameters.__init__(self, ConfigFile)
		self.Rule = [1 if c == 'R' else 0 for c in self.Parameter('Rule')]
		self.Size = int(self.Parameter('Size'))
		self.Noise = int(self.Parameter('Noise'))

class Ant:
	"""Ant agent
	"""
	def __init__(self, Size, Rule, Noise):
		self.Size = Size
		self.VPos = self.Size / 2
		self.HPos = self.Size / 2
		self.VVel = 0
		self.HVel = 1
		self.Cells = {}
		self.Rule = Rule
		self.Cycle = len(self.Rule)
		self.Colours = [2, 1, 0] + list(range(3,13))
		self.Noise = Noise
		self.Steps = 0

	#Update ant position and board state
	def OneStep(self):
		Observer.season()
		state = self.getInfo(self.VPos, self.HPos)
		#Consider noise
		a = random.randint(0,1000000)
		r = self.Rule[state]
		if a < self.Noise:
			r ^= 1
		#Turn ant
		if (r):
			self.turnRight()
		else:
			self.turnLeft()
		state = (state + 1) % self.Cycle
		#Display repainted cell
		Observer.record((self.VPos, self.HPos, self.Colours[state % len(self.Colours)], 1.0/self.Size))
		#Update cell state
		self.Cells[self.VPos, self.HPos] = state
		#Update ant position
		self.VPos = (self.VPos + self.VVel) % self.Size
		self.HPos = (self.HPos + self.HVel) % self.Size
		#Display top right cell to prevent screen resizing
		Observer.record((self.Size, self.Size, self.Colours[self.getInfo(self.Size, self.Size) % len(self.Colours)], 1.0/self.Size))
		self.Steps += 1
		return True

	#Turn ant direction 90 degrees left
	def turnLeft(self):
		turnDict = {(1,0) : (0,1), (0,1) : (-1,0), (-1,0) : (0,-1), (0,-1) : (1,0)}
		self.VVel, self.HVel = turnDict[self.VVel, self.HVel]

	#Turn ant direction 90 degrees right
	def turnRight(self):
		turnDict = {(1,0) : (0,-1), (0,-1) : (-1,0), (-1,0) : (0,1), (0,1) : (1,0)}
		self.VVel, self.HVel = turnDict[self.VVel, self.HVel]

	#Returns the state of the cell at (HPos, VPos), cells are 0 by default
	def getInfo(self, VPos, HPos):
		if (VPos, HPos) in self.Cells:
			return self.Cells[(VPos, HPos)]
		else:
			return 0


if __name__ == "__main__":


	#############################
	# Global objects			#
	#############################
	Scenario = CA_Scenario('_Params.evo')
	CAnt = Ant(Scenario.Size, Scenario.Rule, Scenario.Noise)

	Observer = EO.Generic_Observer()	  # Observer records display orders
	Observer.recordInfo('FieldWallpaper', 'white')
	margin = 4	# horizontal margins in the window
	zoom = 4
	Observer.recordInfo('DefaultViews', [('Field', CAnt.Size * zoom + 2 * margin)])
	steps = 0

	EW.Start(CAnt.OneStep, Observer, Capabilities='RP')		# R means that only changed positions have to be displayed; P enables photos


	print("Simulation over after ", CAnt.Steps, " steps")

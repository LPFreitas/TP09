#!/usr/bin/env python3

""" @brief 	Illustration of Preferential attachment to build scale-free networks
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
# Illustration of Preferential attachment to build scale-free networks                                                                       #
##############################################################################

import sys
from time import sleep
import random
import re
import math
		
sys.path.append('..')
sys.path.append('../../..')
import Evolife.Scenarii.Parameters			as EPar
import Evolife.Ecology.Observer				as EO
import Evolife.Graphics.Evolife_Window	as EW
import Evolife.Tools.Tools					as ET


LinkAspect = ('green3', 1)
NodeAspect = ('red', 4)

	
class Graph_Observer(EO.Observer):
	""" Stores global variables for observation
	"""
	def __init__(self, Scenario):
		EO.Observer.__init__(self, Scenario)
		self.Trajectories = []	# stores temporary changes
		self.Positions = []
		# self.recordInfo('CurveNames', [('yellow', 'Year (each ant moves once a year on average)')])
		self.MsgLength = dict()

	def recordChanges(self, Info, Slot='Positions'):
		# stores current changes
		# Info is a couple (InfoName, Position) and Position == (x, y) or a longer tuple
		if Slot ==  'Positions':	self.Positions.append(Info)
		elif Slot == 'Trajectories':	self.Trajectories.append(Info)
		else:	ET.error('Hyperlinks Observer', 'unknown slot')

	def get_info(self, Slot, default=None):
		"""	this is called when display is required 
		"""
		if Slot == 'Trajectories':
			CC = self.Trajectories
			self.Trajectories = []
			return tuple(CC)
		else:	return EO.Observer.get_info(self, Slot, default=default)

	def get_data(self, Slot, Consumption=True):
		if Slot == 'Field':
			CC = self.Positions
			print(CC)
			self.Positions = []
			return tuple(CC)
		else:	return EO.Observer.get_data(self, Slot)

class Node:
	"""	Defines a node of the network
	"""
	def __init__(self, nodeIndex, Name, Location):
		self.Index = nodeIndex
		self.Name = Name
		self.Location = Location	# physical location
		self.Neighbours = [] # Links to other nodes
	
	def degree(self):
		return len(self.Neighbours)

	def index(self):	return self.Index

	def addNeighbour(self, OtherNode):
		self.Neighbours.append(OtherNode)
	
	def draw(self):	return self.Location + NodeAspect

	def __lt__(self, other):	return  self.Name < other.Name	# just for display
	
	def __str__(self):	return self.Name + str(self.Location)
		


class Graph:

	def __init__(self, Observer, Size=100, NbNodes=100, LinksPerNode=1, Strategy='random', MaxSample=100):
		
		self.Observer = Observer
		self.Nodes = []
		self.Links = []
		self.LinksPerNode = LinksPerNode
		self.TotalNbNodes = NbNodes
		self.CurrentIndex = 0
		self.Strategy = Strategy
		self.MaxSample = MaxSample
	
		self.radius = (Size - 10)/2
		self.center = (Size/2, Size/2)
		self.theta = 2*math.pi/NbNodes
		
		self.initialize()

	def initialize(self):
		for nodeIndex in range(self.TotalNbNodes):	self.createNode(nodeIndex)
		random.shuffle(self.Nodes)	# change visit order
		# giving random neighbours to the first node
		for i in range(self.LinksPerNode):
			while not self.addLink(self.Nodes[0], random.choice(self.Nodes)):	pass
		self.CurrentIndex = 1	# next node to propcess
		
	def createNode(self, nodeIndex=None):
		if nodeIndex is None:	nodeIndex = len(self.Nodes)
		NewNode = Node(nodeIndex, 'N%d' % nodeIndex, (self.center[0]+self.radius*math.cos(nodeIndex*self.theta), self.center[1]+self.radius*math.sin(nodeIndex*self.theta)))
		self.Nodes.append(NewNode)
		Observer.recordChanges((NewNode.Name, NewNode.draw()), Slot='Positions')
		return NewNode
	
	def addLink(self, Node1, Node2):
		if(Node1 in Node2.Neighbours or Node1 == Node2):	return False
		Node1.addNeighbour(Node2)
		Node2.addNeighbour(Node1)
		self.Links.append((Node1, Node2))
		Observer.recordChanges(('L%d' % len(self.Links), (Node1.draw() + Node2.Location + LinkAspect)), Slot='Positions')
		if(len(self.Links)%5 == 0):	self.generateCurve()
		return True
		
	def addNewLink(self):
		self.Observer.season()
		if(self.CurrentIndex == self.TotalNbNodes):	return False
		nodeIndex = self.CurrentIndex
		self.CurrentIndex += 1
		for i in range(self.LinksPerNode):
			neighbour = self.findNeighbour()
			while not self.addLink(self.Nodes[nodeIndex], neighbour):
				neighbour = self.findNeighbour()	# let's try again
		return True

	def findNeighbour(self):
		
		if self.Strategy.upper() in [1, 'PA']:
			#PREFERENTIAL ATTACHMENT
			nbEncounters = random.randint(2, self.MaxSample)
			# Sampling the population
			encounters = [[N, 0] for N in random.sample(self.Nodes, nbEncounters)]
			# determining who is popular in the sample
			for i in range(len(encounters)):
				for OtherIndividualInTheSample, Pop in encounters:
					if OtherIndividualInTheSample in encounters[i][0].Neighbours:
						encounters[i][1] += 1
			random.shuffle(encounters)	# in case there are several best candidates
			return max(encounters, key=lambda x: x[1])[0]
			
		elif self.Strategy.lower() in [2, 'pick']:
			#PICKING STRATEGY
			# vvvvvvvv  To be changed vvvvvvvv
			# use self.Links, which a list of couples representing all edges in the graph
			return random.choice(self.Nodes)	# to be changed
			# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
		elif self.Strategy.lower() in [0, 'random']:
			#RANDOM ATTACHMENT
			return random.choice(self.Nodes)
			
		else:	ET.error('Unknown attachment strategy', self.Strategy)

	def generateCurve(self):
		SortedDegrees = []
		for Node in self.Nodes:
			degree = Node.degree()
			while(len(SortedDegrees) <= degree):
				SortedDegrees.append(0)
			SortedDegrees[degree] += 1
		print('Degree distribution:', SortedDegrees)
		for i in range(self.LinksPerNode, len(SortedDegrees)):
			Observer.recordChanges(('P%d' % i, (math.log(i-self.LinksPerNode+1, 2), math.log(SortedDegrees[i]+1, 2), 'blue', 12)), Slot='Trajectories')


if __name__ == "__main__":
	print(__doc__)
	
	#############################
	# Global objects	    #
	#############################
	Gbl = EPar.Parameters('_Params.evo')	# Loading global parameter values
	
	Observer = Graph_Observer(Gbl)   # Observer contains statistics
	Observer.recordInfo('DefaultViews', [('Field', Gbl.Parameter('DisplaySize'), Gbl.Parameter('DisplaySize')), ('Trajectories', 20, 500, 750, 500), 'Help'])
	Observer.recordInfo('FieldWallpaper', 'lightblue')
	Observer.recordInfo('TrajectoriesWallpaper', 'yellow')
	Observer.recordInfo('FieldTitle', 'Network')
	Observer.recordInfo('TrajectoriesTitle', 'Degree distribution')

	Grph = Graph(Observer, Size=Gbl.Parameter('DisplaySize'), NbNodes=Gbl.Parameter('NumberOfNodes'), LinksPerNode=Gbl.Parameter('LinksPerNode'), Strategy=Gbl.Parameter('Strategy'), MaxSample=Gbl.Parameter('SampleSize'))

	EW.Start(Grph.addNewLink, Observer, Capabilities='RPT')

	# print("Bye.......")
	# sleep(1.0)

__author__ = 'Felix Richart'

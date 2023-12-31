#!/usr/bin/env python3

""" @brief  Gets data from various modules and stores them for display and statistics.
	
	- Generic_Observer --> interface between simulation and window system
	- Experiment_Observer --> idem + headers to store curves

	- Storage --> stores vectors
	- Examiner --> different Storages, one per slot
	- Meta_Examiner --> stores similar Examiners with sames slots + statistics

	- Observer --> Meta_Examiner + Experiment_Observer
	- EvolifeObserver --> specific observer (knows about genomes, phenomes, ...)
	
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
#  Observer                                                                  #
##############################################################################



import sys
import os
import socket
import random

if __name__ == '__main__':  sys.path.append('../..')

import functools 
from time import strftime
from Evolife.Tools.Tools import transpose, error



class Curve:
	"""	Legend of a curve (color, text)
		for Experiment_Observer
	"""
	def __init__(self, Name='Curve', Color='red', Thickness=3, Legend=''):
		self.Name = Name
		self.Color = Color
		self.Thickness = Thickness if Thickness is not None else 3
		self.Legend = Legend
		self.Value = 0

class Curves:
	"""	Legend of a curves
		for Experiment_Observer
	"""
	def __init__(self):
		"""	merely calls reset
		"""
		self.reset()
		
	def reset(self):
		"""	Defines Curves and their current Values
			Stores curves' designation and legend
		"""
		self.Curves = dict()
		self.Values = dict()	# current values of Curves
		self.Colors = []
		self.Designations = []
		self.Legends = []
		
	def append(self, Name='Curve', Color='red', Thickness=3, Legend=''):
		"""	Creates a new (local) curve and stores it
		"""
		if Color not in self.Colors:
			# print(f'adding curve {Name} with color {Color} and thickness {Thickness}: {Legend}')
			if not Legend:	Legend = Name
			self.Curves[Name] = Curve(Name, Color=Color, Thickness=Thickness, Legend=Legend)
			self.Colors.append(Color)
			self.Designations.append((Color, Name, Legend))
			self.Legends.append((Color, Legend))
			self.Values[Name] = None
		else:	error('Observer', 'Two curves with same colour: "%s" already in %s' % (Color, self.Colors))
		
	def Color(self, Name):	
		"""	returns the color of a curve
		"""
		return self.Curves[Name].Color

	def Thickness(self, Name):	
		"""	returns the color of a curve
		"""
		return self.Curves[Name].Thickness
	
	def Value(self, Name, Value=None):	
		"""	sets or returns a curve's current value
		"""
		if Value is not None:	
			self.Values[Name] = Value
		return self.Values[Name]
	
	def legend(self):
		"""	return legends
		"""
		return self.Legends
	
	def CurveNames(self):	
		"""	returns curves' designations
		"""
		return self.Designations
	
	def __iter__(self):	
		"""	iterates through curves
		"""
		return iter(self.Curves.keys())

	# def __contains__(self, Name):	return Name in self.Names
	
	def Orders(self, x):
		"""	Returns current curves' values (at time x)
		"""
		Point = lambda v: v if isinstance(v, tuple) else (x, v)
		return [(self.Color(C), Point(self.Values[C]), self.Thickness(C)) for C in self.Curves if self.Values[C] is not None]

	def __str__(self):	return str(self.Designations)

class Storage:
	"""	Kind of matrix. Stores raw data, typically vectors of integers  
	"""

	def __init__(self, Name):
		"""	calls reset
		"""
		self.Name = Name
		self.reset(0)

	def reset(self, length = -1):
		"""	initializes the 'storage', 'average' and 'best' lists
		"""
		self.open = False
		self.storage = []  # contains data as they arrive (list of vectors)
		self.average = []   # one average vector
		self.best = []  # the best vector
		self.length = length	# number of vectors or items stored
		self.itemLength = -1	# length of item stored

	def open_(self, length = -1):
		"""	marks the storage as 'open'
		"""
		if self.open:
			error('Observer: ',self.Name+': opened twice')
		self.open = True
		self.length = length
		
	def store(self, vector):
		"""	stores a vecor in the storage
		"""
		if not self.open:
			error('Observer: ',self.Name+': not open')
		self.storage.append(vector)
		try:
			if self.itemLength > 0 and len(vector) != self.itemLength:
				error('Observer: ', self.Name + ': Inconsistent item length')
			self.itemLength = len(vector)
		except (AttributeError, TypeError):
			self.itemLength = 1

	def statistics(self):
		"""	to be overloaded
		"""
		pass
	
	def close_(self):
		"""	sets the storage as 'closed'
		"""
		if not self.open:   error('Observer: ', self.Name+': closing while not open')
		if self.length < 0: self.length = len(self.storage)
		elif self.length != len(self.storage):
			error('Observer: ', self.Name+': Inconsistent lengths')
		self.statistics()	# computes statistics 
		self.open = False

	def get_data(self):
		"""	returns a tuple of all the vectors in the storage
		"""
		return tuple([tuple(T) for T in self.storage])
#		return [tuple(T) for T in self.storage]

	def __str__(self):
		return self.Name + \
			'.\tBest:\t' + ' -- '.join(["%.2f" % x for x in self.best]) + \
			'\n' + self.Name + \
			'.\tAvg:\t' + ' -- '.join(["%.2f" % x for x in self.average])

class NumericStorage(Storage):
	"""	Storage + basic statistics 
	"""
	def statistics(self):
		"""	computes best and average
		"""
		TStorage = transpose(self.storage)
		self.best = list(map(lambda x: max(x), TStorage))
		if self.length <= 0:
			return (0,0,0,[])
		self.average = list(map(lambda x: sum(x,0.0)/len(self.storage), TStorage))

		return (len(self.storage), self.best, self.average, tuple(self.get_data()))
	   
class Examiner:
	""" Groups several storages in different slots with different names.
		Use by calling in sequence:
		reset()
		open_(size)		size = number of slots
		store(Slotname, Value, Numeric)	any time  
		close_()	--> this performs statistics for each numeric slot
	"""

	def __init__(self, Name=''):
		"""	initializes a dict of storages
		"""
		self.Name = Name
		self.storages = dict()

	def reset(self, length=-1):
		"""	resets all storages
		"""
		for S in self.storages:
			self.storages[S].reset(length)

	def open_(self, length=-1):
		"""	opens all storages
		"""
		for S in self.storages:
			self.storages[S].open_(length)

	def store(self, StorageName, vector, Numeric=True):
		"""	stores a data vector into a slot named StorageName
		"""
		if StorageName not in self.storages:
			# creating a new slot
			if Numeric:
				self.storages[StorageName] = NumericStorage(StorageName)
			else:
				self.storages[StorageName] = Storage(StorageName)
			self.storages[StorageName].open_()
		self.storages[StorageName].store(vector)

	def statistics(self):
		"""	performs statistics in all individual storages
		"""
		for S in self.storages:
			self.storages[S].statistics()

	def close_(self):
		"""	closes all storages
		"""
		for S in self.storages:
			self.storages[S].close_()

	def display(self, StorageName):
		"""	displays all storages as text, one per line
		"""
		return self.storages[StorageName].__str__()

	def get_data(self, StorageName):
		"""	retrieves a data vector from slot named StorageName
		"""
		try:
			return storages[StorageName].get_data()
		except KeyError:
			return None
			#error('Observer: ',self.Name + ': Accessing unknown observation slot in examiner')
	
	def __str__(self):
		return self.Name + ':\n' + '\n'.join([self.display(S) for S in self.storages])
					

class Meta_Examiner(Storage):
	""" Meta storage: stores several lower-level examiners
		having same slots and performs weighted statistics for each slot
	"""

	def __init__(self, Name=''):
		"""	Defines a storage that will contain various examiners (which are dicts of storages)
			All examiners are supposed to have the same slots (low-level storages)
		"""
		Storage.__init__(self, Name)	# will contain various Examiners
		self.Statistics = dict()
		
	def statistics(self):
		"""	gathers data from the stored examiners
			and stores them as a dictionary of tuples (a tuple per slot)
			(number_of_instances, best_of_each_coordinate,
			 average_of_each_coordinate, list_of_instances) 
		"""
		# one takes the first examiner as representative
		for Slot in self.storage[0].storages:
			if len(list(set([Exam.storages[Slot].itemLength for Exam in self.storage]))) > 1:
				error('Observer: ',self.Name + ': Inconsistent item length accross examiners')
			# computing the best value of each coordinate
			best = list(map(lambda x: max(x), transpose([Exam.storages[Slot].best \
													for Exam in self.storage])))
			# computing the total number of individual data
			cumulative_number = sum([Exam.storages[Slot].length for Exam in self.storage])
			# computing global statistics by summing averages weighted by corresponding numbers
			totals = transpose([list(map(lambda x: x*Exam.storages[Slot].length,
						  Exam.storages[Slot].average)) for Exam in self.storage])
			if cumulative_number:
				average = list(map(lambda x: sum(x)/cumulative_number, totals))
			else:
				average = list(map(lambda x: sum(x), totals))
			self.Statistics[Slot] = {'length':	cumulative_number, 
									  'best':	best,
									  'average':average,
									  'data':	functools.reduce(lambda x,y: x+y, 
													 tuple(tuple(Exam.storages[Slot].storage 
														  for Exam in self.storage)))}
		return self.Statistics

	def get_data(self, Slot):	
		"""	Performs statistics on storage 'Slot'
		"""
		try:
			return tuple(self.Statistics[Slot]['data'])
		except KeyError:
			return None
			#error('Observer: ', self.Name + self.Slot + ': Accessing unknown observation slot in meta-examiner')


class Generic_Observer:
	"""	Minimal observer 
	"""
	def __init__(self, ObsName='', TimeLimit=10000):
		"""	initializes ScenarioName, EvolifeMainDir, CurveNames, Title, Field_grid and Trajectory_grid
		"""
		self.TimeLimit = TimeLimit
		self.DispPeriod = 1
		self.StepId = 0	 # computational time
		self.PreviousStep = -1
		self.Infos = dict()  # will record specific information about the simulation
		self.recordInfo('ScenarioName', ObsName)
		self.recordInfo('EvolifeMainDir', os.path.dirname(sys.argv[0]))
		self.recordInfo('CurveNames', ())
		self.setOutputDir('.')
		self.recordInfo('Title', ObsName)  # minimum x-value when computing curve average  
		self.recordInfo('ResultOffset', 0)  # minimum x-value when computing curve average  
		self.TextErase()
		self.Curves = Curves()	# stores curve legends 
		self.Field_buffer = self.Field_grid()
		self.Trajectory_buffer = self.Trajectory_grid()
		
	def DisplayPeriod(self, Per=0):
		"""	sets or retrieves display period
		"""
		if Per:	self.DispPeriod = Per
		return self.DispPeriod

	def season(self, year=None):
		"""	increments StepId
		"""
		if year is not None:	self.StepId = year
		else:	self.StepId += 1
		return self.StepId
		
	def Visible(self):
		""" decides whether the situation should be displayed 
		"""
		# Have we reached a display point ?
		if self.StepId != self.PreviousStep:
			# print(self.StepId, self.DispPeriod)
			return (self.StepId % self.DispPeriod) == 0
		return False

	def Over(self):
		""" Checks whether time limit has been reached
			and has not been manually bypassed
		"""
		if self.TimeLimit > 0:
			return (self.StepId % self.TimeLimit) >= self.TimeLimit-1 
		return False
		#return self.StepId > self.TimeLimit and self.Visible() \
		#	   and ((self.StepId+1) % self.TimeLimit) < abs(self.DispPeriod)
		#		and self.Visible() \
					
	def setOutputDir(self, ResultDir='___Results'):
		"""	set output directory ('___Results' by default)
		"""
		self.recordInfo('OutputDir', ResultDir)
		if not os.path.exists(ResultDir):
			os.mkdir(ResultDir)
		# Result file name changes
		if self.get_info('ResultFile'):
			self.recordInfo('ResultFile', os.path.join(ResultDir, os.path.basename(self.get_info('ResultFile'))))

	def recordInfo(self, Slot, Value):
		"""	stores Value in Slot
		"""
		# print(Slot, Value)
		self.Infos[Slot] = Value
	
	def get_info(self, Slot, default=None, erase=False):
		"""	returns factual information previously stored in Slot
			returns 'default' (which is None by default) if Slot is not found
		"""
		if Slot == 'PlotOrders':
			return self.GetPlotOrders()
		elif Slot == 'CurveNames':	
			CN = self.Infos[Slot]	# backward compatibility
			return CN if CN else self.CurveNames()
		try:	
			Result = self.Infos[Slot]
			if erase:	del self.Infos[Slot]
			return Result
		except KeyError:	return default

	# def getinfo(self, *p, **pp):	# compatibility
		# return self.get_info(*p, **pp)
		
	def inform(self, Info):
		"""	Info is sent by the simulation -
			Typically a single char, corresponding to a key pressed
			Useful to customize action 
		"""
		pass
	
	def ResultHeader(self):
		"""	Parameter names are stored with the date in the result file header
			Header is just the string "Date" by default
		"""
		return 'Date;\n'

	def record(self, Position, Window='Field', Reset=False):
		"""	stores current position changes into the Window's buffer ('Field' by default, could be 'Trajectories')
			'Position' can also be the string "erase"
		"""
		if isinstance(Position, list):	Buffer = list(Position)
		elif isinstance(Position, tuple):	Buffer = [Position]
		elif Position.lower() == 'erase':	Buffer = ['erase']	# order to erase the window
		else:	error('Observer', "Should be 'erase' or tuple or list: " + str(Position))
		Keep = not Reset
		if Window == 'Field':			self.Field_buffer = Keep * self.Field_buffer + Buffer
		elif Window == 'Trajectories':	self.Trajectory_buffer = Keep * self.Trajectory_buffer + Buffer

	# initial drawings
	def Field_grid(self):
		""" returns initial drawing for 'Field'
		"""
		return []
		
	def Trajectory_grid(self):	
		""" returns initial drawing for 'Trajectories'
		"""
		return []
		
	def get_data(self, Slot, Consumption=True):
		"""	Retrieves data from Slot.
			Erases Slot's content if Consumption is True
		"""
		if Slot in ['Positions', 'Field']:
			# emptying Field_buffer 
			CC = self.Field_buffer
			if Consumption:	self.Field_buffer = []
			return tuple(CC)
		elif Slot == 'Trajectories':
			# emptying Trajectory_buffer
			CC = self.Trajectory_buffer
			if Consumption:	self.Trajectory_buffer = []
			if CC:	return tuple(CC)
			return self.get_info(Slot)	# retro-compatibility
		return None
		
	def displayed(self):
		"""	Remembers that display occurred (to ensure that it answers once a year)
		"""
		self.PreviousStep = self.StepId # to ensure that it answers once a year 

	def TextErase(self):
		"""	Erases the text buffer
		"""
		self.__TxtBuf = ""

	def TextDisplay(self, Str=""):
		"""	stores a string that will be displayed at appropriate time.
			Text is currently printed on the console (to be changed)
		"""
		self.__TxtBuf += Str
		print(self.__TxtBuf)	# to be changed
		self.TextErase()
		return self.__TxtBuf

	def curve(self, Name=None, Value=None, Color=None, Thickness=None, Legend=None):
		"""	creates or retrieves a curve or return curve's current value.
			If Name is None: resets all curves.
		"""
		if Name is None:
			for C in self.Curves:	C.reset()
			self.Curves.reset()
			return None
		if Color is not None and Name not in self.Curves:	
			self.Curves.append(Name, Color=Color, Thickness=Thickness, Legend=Legend)
		return (self.Curves.Color(Name), self.Curves.Value(Name, Value))
		
	def legend(self):
		"""	returns curves' legends
		"""
		return self.Curves.legend()
	
	def CurveNames(self):	
		"""	returns curves' names
		"""
		return self.Curves.CurveNames()
	
	def GetPlotOrders(self):
		"""	Returns current curves' values if observer in visible state
		"""
		# print(self.Curves.Orders(self.StepId))
		if self.Visible():
			return self.Curves.Orders(self.StepId)
		return []
	
	def __str__(self):
		Str = self.get_info('Title') + '\nStep: ' + str(self.StepId)
		return Str
		
class Experiment_Observer(Generic_Observer):
	"""	Typical observer for an experiment with parameters
	"""

	def __init__(self, ParameterSet):
		"""	Initializes ScenarioName, EvolifeMainDir, CurveNames, Title, Field_grid and Trajectory_grid
			Sets DisplayPeriod, TimeLimit, Icon, ... from values taken from ParameterSet
			ExperienceID is set to current date
			Sets ResultFile (appends ExperienceID in batch mode)
		"""
		self.ParamSet = ParameterSet
		self.Parameter = ParameterSet.Parameter
		Title = self.Parameter('Title', Default='Evolife').replace('_', ' ')
		Generic_Observer.__init__(self, Title)
		self.recordInfo('ScenarioName', self.Parameter('ScenarioName'))
		self.DispPeriod = self.Parameter('DisplayPeriod')
		self.TimeLimit = self.Parameter('TimeLimit')
		self.recordInfo('ExperienceID', strftime("%y%m%d%H%M%S"))
		self.recordInfo('Icon', self.Parameter('Icon', Default=None))
		CurveOffset = self.Parameter('DumpStart', Default=0)	# minimum x-value when computing curve average  
		if type(CurveOffset) == str and CurveOffset.strip().endswith('%'):	# Offset expressed in % of TimeLimit
			CurveOffset = (self.TimeLimit * int(CurveOffset.strip('%'))) // 100
		self.recordInfo('ResultOffset', CurveOffset)  	# to ignore transitory regime in curves
		self.BatchMode = self.Parameter('BatchMode', Default=0)
		if self.BatchMode:
			machine = socket.gethostname().split('.')[0]
			self.recordInfo('ResultFile', f"___{self.get_info('ScenarioName')}_{self.get_info('ExperienceID')}_{machine}_{random.randint(0,99):02}")
		else:
			self.recordInfo('ResultFile', f"___{self.get_info('ScenarioName')}_")
		if self.Parameter('ResultDir', Default=None) is not None:
			self.setOutputDir(self.Parameter('ResultDir'))
		else:	self.setOutputDir()	# default

	def ResultHeader(self):
		"""	Relevant parameter names are stored into the result file header, juste after the string "Date"
			Parameter values are added just below the header
		"""
		Header = 'Date;' + ';'.join(self.ParamSet.RelevantParamNames()) + ';\n'
		# adding parameter values to result file
		Header += self.get_info('ExperienceID') + ';'
		Header += ';'.join([str(self.Parameter(P, Silent=True))
									  for P in self.ParamSet.RelevantParamNames()]) + ';'
		return Header
		
	# def get_info(self, Slot, *p, **pp):
	def get_info(self, Slot, default=None):
		"""	returns factual information previously stored in Slot.
			default value is None by default
		"""
		# Header is computed by the time of the call, as relevant parameters are not known in advance
		if Slot == 'ResultHeader':
			return self.ResultHeader()
		# return Generic_Observer.get_info(self, Slot, *p, *pp)
		return Generic_Observer.get_info(self, Slot, default=default)


class Observer(Meta_Examiner, Experiment_Observer):
	""" Contains instantaneous data updated from the simulation
		for statistics and display
	"""
	
	def __init__(self, Scenario=None):
		"""	calls Experiment_Observer constructor if Scenario is not None, Generic_Observer otherwise
			calls Meta_Examiner constructor
		"""
		self.Scenario = Scenario
		if Scenario:	Experiment_Observer.__init__(self, Scenario)
		else:	Generic_Observer.__init__(self)
		Meta_Examiner.__init__(self)

	def get_data(self, Slot, Consumption=True):	
		"""	Retrieves data stored in Slot from Experiment_Observer (or, if None, from Meta_Examiner)
		"""
		Data = Experiment_Observer.get_data(self, Slot, Consumption=Consumption)
		if not Data:
			Data = Meta_Examiner.get_data(self, Slot)
		return Data
		
		
class EvolifeObserver(Observer):
	""" Evolife-aware observer based on the use of a scenario.
		Retrieves curves' names and legends, and satellite window names, legends and wallpapers
		as provided by scenario
		Contains instantaneous data updated from the simulation
		for statistics and display
	"""
	
	def __init__(self, Scenario):
		Observer.__init__(self, Scenario)
		try:	self.Parameter('ScenarioName')  # to make it relevant
		except KeyError:	pass

		# Location of the Evolife Directory
		# for R in os.walk(os.path.abspath('.')[0:os.path.abspath('.').find('Evo')]):
			# if os.path.exists(os.path.join(R[0], 'Evolife', '__init__.py')):
				# self.recordInfo('EvolifeMainDir', os.path.join(R[0], 'Evolife'))	# location of the main programme
				# break
		self.recordInfo('GenePattern', self.Scenario.gene_pattern())
		for Window in ['Field', 'Curves', 'Genome', 'Log', 'Help', 'Trajectories', 'Network']:
			self.recordInfo(Window + 'Wallpaper', self.Scenario.wallpaper(Window))
		self.recordInfo('DefaultViews', self.Scenario.default_view())
		self.recordInfo('WindowLegends', self.Scenario.legends())
		# declaring curves
		for Curve_description in self.Scenario.display_():
			(Colour, Name, Legend, Thickness) = Curve_description + (0, '', '', 3)[len(Curve_description):]
			if not Legend:
				if Name in self.Scenario.get_gene_names():	Legend = f'Average value of gene {Name} in the population'
				elif Name in self.Scenario.phenemap():		Legend = f'Average value of phene {Name} in the population'
			self.curve(Name=Name, Color=Colour, Legend=Legend, Thickness=Thickness)

	def GetPlotOrders(self):
		""" Gets the curves to be displayed from the scenario and
			returns intantaneous values to be displayed on these curves
		"""
		PlotOrders = []

		for Curve in self.Curves:
			if Curve == 'best':
				value = self.Statistics['Properties']['best'][1]
			elif Curve == 'average':
				value = self.Statistics['Properties']['average'][1]
			elif Curve in self.Scenario.get_gene_names():
				# displaying average values of genes
				value = self.Statistics['Genomes']['average'][self.Scenario.get_locus(Curve)]
			elif Curve in self.Scenario.phenemap():
				# displaying average values of phenes
				value = self.Statistics['Phenomes']['average'][self.Scenario.phenemap().index(Curve)]
			else:	# looking for Curve in Scenario's local variables
				if Curve in dir(self.Scenario):
					try:	value = int(getattr(self.Scenario, Curve))
					except TypeError:	
						error(self.Name, ": bad value for " + Curve)
				else:
					error(self.Name, ": unknown display instruction: " + Curve)
					value = 0
			self.curve(Curve, int(value))
		return Observer.GetPlotOrders(self)

	def get_info(self, Slot, default=None):
		"""	returns factual information previously stored in Slot
		"""
		if Slot == 'Trajectories':
			Best= self.get_info('Best', default=default)
			if Best is not None:	return Best
		return Observer.get_info(self, Slot, default=default)

	def TextDisplay(self, Str=""):
		""" stores a string that will be displayed at appropriate time
		"""
		if not self.BatchMode:
			return Experiment_Observer.TextDisplay(self,Str)
		else:   # do nothing
			return ''
		
	def Field_grid(self):
		""" returns initial drawing for 'Field'
		"""
		return self.Scenario.Field_grid()
	def Trajectory_grid(self):
		""" returns initial drawing for 'Trajectories'
		"""
		return self.Scenario.Trajectory_grid()
	
	def __str__(self):
		Str = self.Name + '\nStep: ' + str(self.StepId) + \
			   '\tIndividuals: ' + str(self.Statistics['Genomes']['length']) + \
			   '\tBest: '	+ "%.2f" % self.Statistics['Properties']['best'][1]  + \
			   '\tAverage: ' + "%.2f" % self.Statistics['Properties']['average'][1] + '\n'
		Str += '\n'.join([gr.display('Properties') for gr in self.storage])
		return Str


if __name__ == "__main__":
	print(__doc__)
	BO = Examiner('basic_obs')
	BO.store('Slot1',[1,2,3,8,2,6])
	BO.store('Slot1',[9,8,7,5,0,2])
	BO.store('Slot1',[8,8,8,3,1,2])
	BO.store('Slot2',[7,8,9])
	BO.store('Slot2',[9,8,7])
	BO.store('Slot2',[8,8,8])
	BO.close_()
	print(BO)
	BO2 = Examiner('basic_obs2')
	BO2.store('Slot1',[10,18,27,1,1,1])
	BO2.store('Slot2',[10,10,10])
	BO2.close_()
	print(BO2)
	MBO = Meta_Examiner('Meta_Obs')
	MBO.open_(2)
	MBO.store(BO)
	MBO.store(BO2)
	MBO.close_()
	print(MBO)
	print(MBO.statistics())
	
	raw_input('[Return]')


__author__ = 'Dessalles'

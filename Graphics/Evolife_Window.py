#!/usr/bin/env python3

""" @brief  Evolife Window system                                                 """

#============================================================================#
# EVOLIFE  http://evolife.telecom-paris.fr             Jean-Louis Dessalles  #
# Telecom Paris  2023-11-19                                www.dessalles.fr  #
# -------------------------------------------------------------------------- #
# License:  Creative Commons BY-NC-SA                                        #
#============================================================================#
# Documentation: https://evolife.telecom-paris.fr/Classes                    #
#============================================================================#

##############################################################################

import sys
if __name__ == '__main__':  sys.path.append('../..')  # for tests

try:	from PyQt5 import QtGui, QtCore, QtWidgets
except ImportError:				# compatibility with PyQt4
		from PyQt4 import QtGui, QtCore
		from PyQt4 import QtGui as QtWidgets

import webbrowser   # is user clicks on link
import math
import os.path
import random

from Evolife.Graphics import Plot_Area 
from Evolife.Graphics import Evolife_Graphic
from Evolife.Graphics import Simulation_Thread		# Thread to run the simulation in parallel
from Evolife.Graphics import Screen					# Physical screens
from Evolife.Tools.Tools import EvolifeError

DefaultIconName = 'Graphics/EvolifeIcon.png'
HelpFileName = 'Help.txt'
EvolifeURL = 'http://evolife.telecom-paris.fr'



##################################################
# Interface with the simulation thread           #
##################################################

class Simulation_Control:
	""" Controls the simulation, either step by step, or in
		a continuous mode.
	"""

	def __init__(self, SimulationStep, Obs, method='timer'):
		"""	Stores Obs as observer 
			and SimulationStep as the function that processes one step of the simulation.
			'method' can be 'timer' or 'thread' ('timer' preferred)
		"""
		self.Obs = Obs  # simulation observer
		self.SimulationStep = SimulationStep   # function that launches one step of the simulation
		self.method = method	# should be either 'timer' or 'thread'
		self.timer = None   # using a timer is one way of running simulation
		
		## Status of the simulation programme
		self.simulation = None  			# name of the simulation thread
		self.simulation_steady_mode = False	# true when simulation is automatically repeated
		self.simulation_under_way = True	# becomes false when the simulation thinks it's really over
		self.previous_Disp_period = self.Disp_period = Obs.DisplayPeriod()	# display period

	def RunButtonClick(self, event=None):
		"""	Entering in 'Run' mode
		"""
		self.Disp_period = self.previous_Disp_period
		self.Obs.DisplayPeriod(self.Disp_period)	# let Obs know
		self.simulation_steady_mode = True	 # Continuous functioning
		self.Simulation_resume()
	
	def StepButtonClick(self, event=None):
		"""	Entering in 'Step' mode
		"""
		self.Disp_period = 1
		self.Obs.DisplayPeriod(self.Disp_period)	# let Obs know
		self.simulation_steady_mode = False	# Stepwise functioning
		self.simulation_under_way = True	# to allow for one more step
		self.Simulation_resume()
	
	def Simulation_stop(self):
		"""	Stops the simulation thread or timer
		"""
		if self.method == 'timer':
			if self.timer is not None and self.timer.isActive():
				self.timer.stop()
		elif self.method == 'thread':
			if self.simulation is not None:
				self.simulation.stop()
				if self.simulation.isAlive():
					#print 'strange...'
					self.simulation = None  # well...
					return False
				self.simulation = None
		return True
		
	def Simulation_launch(self,continuous_mode):
		"""	(re)starts the simulation thread or timer
		"""
		self.Simulation_stop()
		if self.method == 'timer':
			if continuous_mode:
				if self.timer is None:
					self.timer = QtCore.QTimer()
					self.timer.timeout.connect(self.OneStep)
				self.timer.start()
			else:
				self.OneStep()
		elif self.method == 'thread':
			# A new simulation thread is created
			self.simulation = Simulation_Thread.Simulation(self.SimulationStep,continuous_mode, self.ReturnFromThread)
			self.simulation.start()
		return True
		
	def Simulation_resume(self):
		"""	calls Simulation_launch
		"""
		return self.Simulation_launch(self.simulation_steady_mode)	# same functioning as before			
		
	def OneStep(self):
		"""	calls SimulationStep
		"""
		# print('-', end="", flush=True)
		if self.simulation_under_way:
			try:	self.simulation_under_way = self.SimulationStep()
			except EvolifeError:
				self.Simulation_stop()
				import traceback
				traceback.print_exc()
		else:	
			self.StepButtonClick()	# avoids to loop
			self.DecisionToEnd()
		if self.ReturnFromThread() < 0:		# should return negative value only once, not next time
		# if self.ReturnFromThread() < 0:
			# The simulation is over
			#self.Simulation_stop()
			self.StepButtonClick()
		
	def ReturnFromThread(self):
		"""	to be overloaded
		"""
		pass	
	
	def DecisionToEnd(self):
		"""	to be overloaded
		"""
		pass
	


##################################################
# Incremental definition of windows			  #
##################################################

		
Screen_ = None	# to be instantiated in 'Start'

#---------------------------#
# Control panel             #
#---------------------------#

class Simulation_Control_Frame(Simulation_Control, Evolife_Graphic.Active_Frame):
	""" Minimal control panel with [Run] [Step] [Help] and [quit] buttons
	"""
	
	def __init__(self, SimulationStep, Obs):
		"""	Creates a window with buttons that is also a Simulation_Control
		"""
		self.Name = Obs.get_info('Title')
		self.IconName = Obs.get_info('Icon')
		if not self.IconName:	self.IconName = DefaultIconName
		Simulation_Control.__init__(self, SimulationStep, Obs, method='timer')
		Evolife_Graphic.Active_Frame.__init__(self, parent=None, control=self)
		if self.Name:
			self.setWindowTitle(self.Name)
		self.setWindowIcon(QtGui.QIcon(os.path.join(self.Obs.get_info('EvolifeMainDir'), self.IconName)))

		## List and status of Satellite windows
		self.SWindows = dict()
		self.SWindowsPreferredGeometry = dict()
		self.SWindowsMargins = dict()
		self.Finish = False
		self.alive = True
		self.PhotoMode = 0  # no photo, no film
		self.CurrentFrame = 0   # keeps track of photo numbers
		
		# control frame
		self.control_frame = QtWidgets.QVBoxLayout()
		#self.control_frame.setGeometry(QtCore.QRect(0,0,60,100))
		
		# inside control_frame we create two labels and button_frames
		NameLabel = QtWidgets.QLabel("<font style='color:blue;font-size:17px;font-family:Comic Sans MS;font-weight:bold;'>%s</font>" % self.Name.upper(), self)
		NameLabel.setAlignment(QtCore.Qt.AlignHCenter)
		self.control_frame.addWidget(NameLabel)
		AdrLabel = QtWidgets.QLabel(f"<a href={EvolifeURL}>www.dessalles.fr/{self.Name.replace(' ','_')}</a>", self)
		AdrLabel.setAlignment(QtCore.Qt.AlignHCenter)
		AdrLabel.linkActivated.connect(self.EvolifeWebSite)
		self.control_frame.addWidget(AdrLabel)

		# Button names
		self.Buttons = dict()

		# button frame
		self.button_frame = QtWidgets.QVBoxLayout()
		self.control_frame.addLayout(self.button_frame)

		# Creating small button frame
		self.SmallButtonFrame = QtWidgets.QHBoxLayout()
		self.control_frame.addLayout(self.SmallButtonFrame)

		# Creating help button frame
		self.HelpButtonFrame = QtWidgets.QHBoxLayout()
		self.control_frame.addLayout(self.HelpButtonFrame)

		# Creating big buttons
		self.Buttons['Run'] = self.LocalButton(self.button_frame, QtWidgets.QPushButton, "&Run", "Runs the simulation continuously", self.RunButtonClick)   # Run button
		self.Buttons['Step'] = self.LocalButton(self.button_frame, QtWidgets.QPushButton, "&Step", "Pauses the simulation or runs it stepwise", self.StepButtonClick)
		self.control_frame.addStretch(1)
		self.Buttons['Help'] = self.LocalButton(self.HelpButtonFrame, QtWidgets.QPushButton, "&Help", "Provides help about this interface", self.HelpButtonClick)
		self.Buttons['Quit'] = self.LocalButton(self.control_frame, QtWidgets.QPushButton, "&Quit", "Quit the programme", self.QuitButtonClick)
		
		# room for plot panel			#
		self.plot_frame = QtWidgets.QHBoxLayout()
		self.plot_frame.addLayout(self.control_frame)
		#self.plot_frame.addStretch(1)

		self.setLayout(self.plot_frame)
		self.setGeometry(*Screen_.locate(200, 200, 140, 300))		
		self.show()
		

	def LocalButton(self, ParentFrame, ButtonType, Text, Tip, ClickFunction, ShortCutKey=None):
		"""	Creates a button
		"""
		Button = ButtonType(Text, self)
		Button.setToolTip(Tip)
		Button.clicked.connect(ClickFunction)
		if ShortCutKey is not None:
			Button.setShortcut(QtGui.QKeySequence(ShortCutKey))
		ParentFrame.addWidget(Button)
		return Button

	def EvolifeWebSite(self, e):
		"""	opens Web browser with provided address
		"""
		webbrowser.open(e)
		
	def HelpButtonClick(self, event=None):
		"""	Displays a text file named: Help.txt
		"""
		if not 'Help' in self.SWindows:
			self.SWindows['Help'] = Evolife_Graphic.Help_window(self)
			self.SWindows['Help'].setWindowIcon(QtGui.QIcon(os.path.join(self.Obs.get_info('EvolifeMainDir'),self.IconName)))
			try:
				self.SWindows['Help'].display(os.path.join(self.Obs.get_info('EvolifeMainDir'), HelpFileName))
				self.SWindows['Help'].setGeometry(*Screen_.locate(400, 120, 600, 500))		

			except IOError:
				self.Obs.TextDisplay("Unable to find help file %s" % HelpFileName)
				del self.SWindows['Help']
		else:   self.SWindows['Help'].Raise()

	def QuitButtonClick(self, event): 
		"""	closes the window
		"""
		self.close()
##		if self.closeEvent(None):
##			QtCore.QCoreApplication.instance().quit()
		
	def Raise(self):
		"""	puts the window in front of display
		"""
		if self.isActiveWindow():
			for SWName in self.SWindows:
				self.SWindows[SWName].raise_()
			if self.SWindows:
				SWName = random.choice(list(self.SWindows.keys()))
				self.SWindows[SWName].Raise()				
		else:
			self.raise_()
			self.activateWindow()


	def closeEvent(self, event):
		"""	close satelite windows and stops the simulation
		"""
		self.Finish = True
		self.simulation_steady_mode = False	# Stepwise functioning		
		for (SWName,SW) in list(self.SWindows.items()): # items() necessary here; list necessary for python 3
			self.SWindows[SWName].close()		 
		# No more satelite window left at this stage
		self.Simulation_stop()
		event.accept()

	def SWDestroyed(self, SW):
		"""	A satellite window has been destroyed - removes it from the list
		"""
		for SWName in self.SWindows:
			if self.SWindows[SWName] == SW:
				del self.SWindows[SWName]
				return
		error('Evolife_Window', 'Unidentified destroyed window')

	def ReturnFromThread(self):
		"""	Processes graphic orders if in visible state
			returns -1 if Observer says the simulation is over
		"""
		Simulation_Control.ReturnFromThread(self)	# parent class procedure
		if self.Obs.Visible():	self.Process_graph_orders()
		if self.Obs.Over():	return -1	# Stops the simulation thread
		return False

	def Process_graph_orders(self):
		"""	Just let Observer know that display has taken place
		"""
		self.Obs.displayed()  # Let Obs know that display takes place
		self.CurrentFrame += 1			   
		if self.PhotoMode == 1:
			# single shot mode is over
			self.PhotoMode = 0

	def keyPressEvent(self, e):
		"""	processes actions such as Run, Step, Help...
		"""
		if e.key() in [QtCore.Qt.Key_Q, QtCore.Qt.Key_Escape]:
			self.close()		
		elif e.key() in [QtCore.Qt.Key_S, QtCore.Qt.Key_Space]: # Space does not work...
			self.StepButtonClick()
		elif e.key() in [QtCore.Qt.Key_R, QtCore.Qt.Key_C]:
			self.Buttons['Run'].animateClick()
		elif e.key() in [QtCore.Qt.Key_H, QtCore.Qt.Key_F1]:
			self.Buttons['Help'].animateClick()
		elif e.key() in [QtCore.Qt.Key_M]:  # to avoid recursion
			self.Raise()
		# let Obs know
		try:	self.Obs.inform(str(e.text()))
		except UnicodeEncodeError:	pass

	def EventInterpreter(self, Event):
		"""	Sends event to observer (useful for mouse events)
		"""
		# print(Event.EventType, (Event.EmittingClass, Event.Info))
		self.Obs.recordInfo(Event.EventType, (Event.EmittingClass, Event.Info))
		pass

#---------------------------#
# Control panel + Slider    #
#---------------------------#
class Simulation_Display_Control_Frame(Simulation_Control_Frame):
	""" This class combines a control panel and a slider for controlling display period
	"""

	def __init__(self, SimulationStep, Obs, Background=None):
		"""	Create Control frame + displayperiod slider
		"""

		Simulation_Control_Frame.__init__(self, SimulationStep, Obs)

		# DisplayPeriod slider
		self.lcd = QtWidgets.QLCDNumber(self)
		self.lcd.SegmentStyle(QtWidgets.QLCDNumber.Filled)
		lcdPalette = QtGui.QPalette()
		lcdPalette.setColor(QtGui.QPalette.Light, QtGui.QColor(200,10,10))
		self.lcd.setPalette(lcdPalette)
		self.button_frame.addWidget(self.lcd)
		self.DisplayPeriodSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
		self.button_frame.addWidget(self.DisplayPeriodSlider)
		self.DisplayPeriodSlider.valueChanged.connect(self.DisplayPeriodChanged)
		self.DisplayPeriodSlider.setMinimum(0)
		self.sliderPrecision = 5	# decimal precision, as now slider valueChanged events are integers
		self.DisplayPeriodSlider.setMaximum(3 * 10 ** self.sliderPrecision)
		self.DisplayPeriodSet(self.Obs.DisplayPeriod())

	def DisplayPeriodChanged(self, event):
		""" The displayed value varies exponentially with the slider's position
		"""
		disp = int(10 ** ((int(event)+1)/(10.0 ** self.sliderPrecision)))
		if (disp > 2999):   disp = ((disp+500) // 1000) * 1000
		elif (disp > 299):  disp = ((disp+50) // 100) * 100
		elif (disp > 29):   disp = ((disp+5) // 10) * 10
		elif (disp > 14):   disp = ((disp+2) // 5) * 5
		disp = int(disp)
		self.previous_Disp_period = disp
		self.Disp_period = disp
		self.lcd.display(str(disp))
		self.Obs.DisplayPeriod(self.Disp_period)	# let Obs know

	def DisplayPeriodSet(self, Period, FlagForce=True):
		if Period == 0: Period = 1
		Position = int(math.log(abs(Period),10) * 10 ** self.sliderPrecision)
		self.DisplayPeriodSlider.setSliderPosition(Position)
		self.lcd.display(Period)



#---------------------------#
# Control panel + Curves	#
#---------------------------#

class Simulation_Frame(Simulation_Display_Control_Frame):
	""" This class combines a control panel and a space to display curves
	"""

	def __init__(self, SimulationStep, Obs, Background=None):
		"""	Creates a plot area and displays it to the right of the control frame
		"""

		Simulation_Display_Control_Frame.__init__(self, SimulationStep, Obs)
		self.setGeometry(*Screen_.locate(50, 50, 702, 420))		

		##################################
		# plot panel					 #
		##################################
		self.plot_area = Evolife_Graphic.AreaView(AreaType=Plot_Area.Plot_Area, image=Background, zoom=Screen_.ratio)
		self.plot_frame.addWidget(self.plot_area,1)	  
		#self.plot_area.show()
		#self.plot_area.Area.drawPoints()
		# self.Obs.TextDisplay(self.plot_area.Area.Curvenames(self.Obs.get_info('CurveNames')))
		
		# adding legend button
		self.Buttons['Legend'] = self.LocalButton(self.HelpButtonFrame, QtWidgets.QPushButton, "Legen&d", "Displays legend for curves", self.LegendButtonClick)


	def LegendButtonClick(self, event=None):
		"""	Displays a text file named:  
		"""
		if not 'Legend' in self.SWindows:
			self.SWindows['Legend'] = Evolife_Graphic.Legend_window(self)
			self.SWindows['Legend'].setWindowIcon(QtGui.QIcon(os.path.join(self.Obs.get_info('EvolifeMainDir'),self.IconName)))
			try:
				self.plot_area.Area.Curvenames(self.Obs.get_info('CurveNames'))	# stores curve names
				Comments = self.Obs.get_info('WindowLegends')
				# self.SWindows['Legend'].display(self.Obs.get_info('CurveNames'), Comments=Comments)
				self.SWindows['Legend'].display(self.plot_area.Area.Legend(), Comments=Comments)
				self.SWindows['Legend'].setGeometry(*Screen_.locate(50, 550, 600, 150))		

			except IOError:
				self.Obs.TextDisplay("Unable to find information on curves")
				del self.SWindows['Legend']
		else:   
			# self.SWindows['Legend'].Raise()
			self.SWindows['Legend'].close()
			# del self.SWindows['Legend']

	def Process_graph_orders(self):
		"""	Processes graph orders received from observer.
			Displays PlotData by adding points to curves and by displaying them.
		"""
		if self.Finish:	return
		if self.PhotoMode:	# one takes a photo
			ImgC = self.plot_area.photo('___Curves_', self.CurrentFrame, outputDir=self.Obs.get_info('OutputDir'))
			if self.PhotoMode == 1:	# Photo mode, not film
				self.Obs.TextDisplay('%s Created' % ImgC)
				self.dump()
		PlotData = self.Obs.get_info('PlotOrders')
		if PlotData:	
			for CurveData in PlotData:
				CurveData += (3,)[len(CurveData)-2:]	# adding default thickness: 3
				(CurveId, Point, Thickness) = CurveData
				self.plot_area.Area.plot(CurveId, Point, Width=Thickness*Screen_.ratio)
		Simulation_Control_Frame.Process_graph_orders(self)

	def dump(self, verbose=False):
		"""	store and print simulation results	
		"""
		# creates a result file and writes parameter names into it
		RF = self.Obs.get_info('ResultFile')
		if RF:
			self.plot_area.Area.Curvenames(self.Obs.get_info('CurveNames'))	# stores curve names - may have been updated
			AverageValues = self.plot_area.Area.dump(RF, self.Obs.get_info('ResultHeader'), 
										self.Obs.get_info('ResultOffset', 0))
			if verbose:
				self.Obs.TextDisplay('\n. ' + '\n. '.join(['%s\t%s' % (C, AverageValues[C]) for C in sorted(AverageValues)]))
				self.Obs.TextDisplay('\nResults stored in %s*.csv' % os.path.normpath(RF))
		
	def closeEvent(self, event):
		"""	close parent closeEvent
		"""
		if self.alive:	self.dump(verbose=True)
		self.alive = False
		Simulation_Control_Frame.closeEvent(self, event)
		event.accept()

#-------------------------------------------#
# Control panel + Curves + Genomes + . . .  #
#-------------------------------------------#
	  
class Evolife_Frame(Simulation_Frame):
	""" Defines Evolife main window by modification of the generic Simulation Frame
	"""

	def __init__(self, SimulationStep, Obs, Capabilities='C', Options=[]):
		"""	Creation of the main window and active satelite windows
		"""
		###################################
		# Creation of the main window     #
		###################################
		self.Capabilities = list(Capabilities)
		# Determining backagounds
		self.Background = dict()
		self.WindowTitles = dict()
		self.DOptions = dict(Options)
		self.Background['Default'] = "#F0B554"
		if 'Background' in self.DOptions:	# Default background for all windows
			self.Background['Default'] = self.DOptions['Background']
		if Obs.get_info('Background') is not None:
			self.Background['Default'] = Obs.get_info('Background')
		for W in ['Curves', 'Genomes', 'Photo', 'Trajectories', 'Network', 'Field', 'Log', 'Image']:
			self.Background[W] = Obs.get_info(W + 'Wallpaper')
			if self.Background[W] is None:	self.Background[W] = self.Background['Default']
			self.WindowTitles[W] = Obs.get_info(W + 'Title')
			if self.WindowTitles[W] is None:	self.WindowTitles[W] = W
			

		if 'C' in self.Capabilities:
			self.ParentClass = Simulation_Frame
			Simulation_Frame.__init__(self, SimulationStep, Obs, Background=self.Background['Curves'])
		elif set('FRGNT') & set(Capabilities):
			self.ParentClass = Simulation_Display_Control_Frame
			Simulation_Display_Control_Frame.__init__(self, SimulationStep, Obs)
		else:
			self.ParentClass = Simulation_Control_Frame
			Simulation_Control_Frame.__init__(self, SimulationStep, Obs)

		##################################
		# Control panel                  #
		##################################

		# Creating small buttons
		if 'T' in self.Capabilities:
			self.Buttons['Trajectories'] = self.LocalButton(self.SmallButtonFrame, QtWidgets.QCheckBox, "&T", 'Displays trajectories', self.TrajectoryButtonClick, QtCore.Qt.Key_T)
		if 'N' in self.Capabilities:
			self.Buttons['Network'] = self.LocalButton(self.SmallButtonFrame, QtWidgets.QCheckBox, "&N", 'Displays social links', self.NetworkButtonClick, QtCore.Qt.Key_N)
		if set('FRI') & set(self.Capabilities):
			# Region is a kind of field
			self.Buttons['Field'] = self.LocalButton(self.SmallButtonFrame, QtWidgets.QCheckBox, "&F", 'Displays field', self.FieldButtonClick, QtCore.Qt.Key_F)
		if 'L' in self.Capabilities:
			self.Buttons['Log'] = self.LocalButton(self.SmallButtonFrame, QtWidgets.QCheckBox, "&L", 'Displays Labyrinth', self.LogButtonClick, QtCore.Qt.Key_L)

		if 'R' in self.Capabilities:	self.FieldOngoingDisplay = True
		else:	self.FieldOngoingDisplay = False

		# Creating big buttons (they are big for historical reasons)
		if 'G' in self.Capabilities:
			self.Buttons['Genomes'] = self.LocalButton(self.button_frame, QtWidgets.QPushButton, "&Genomes", 'Displays genomes', self.GenomeButtonClick)  # Genome button
		if 'P' in self.Capabilities:
			self.Buttons['Photo'] = self.LocalButton(self.button_frame, QtWidgets.QPushButton, "&Photo", 'Saves a .jpg picture', self.PhotoButtonClick)  # Photo button

		# Activate the main satellite windows
		DefViews = self.Obs.get_info('DefaultViews')
		if DefViews:
			DefViews.reverse()	# surprisingly necessary to get the last window active
			for B in DefViews:
				# two syntaxes allowed: 'WindowName' or tuple: ('Windowname', ...) with optional '*': ('*Windowname', ...)
				# where ... can be:  width [,height...]) 
				# or x, y, width, height 
				# or x, y, width, height, leftmargin, rightmargin, bottommargin,topmargin
				if type(B) == str:	self.Buttons[B].animateClick()
				elif type(B) == tuple:
					windowName = B[0]
					if windowName.startswith('*'):	windowName = windowName[1:]
					else:	self.Buttons[windowName].animateClick()
					# self.Buttons[B[0]].animateClick(*B[1:])
					if len(B) <= 3:	# only dimensions provided
						self.SWindowsPreferredGeometry[windowName] = Screen_.resize(*B[1:])
					else:
						self.SWindowsPreferredGeometry[windowName] = Screen_.locate(*B[1:5])
					if len(B) > 4:	# margins
						self.SWindowsMargins[windowName] = B[5:]
		elif DefViews is None:
			for B in ['Trajectories', 'Field', 'Network', 'Genomes', 'Log']:	# ordered list
				if B in self.Buttons:
					self.Buttons[B].animateClick()
					break	# opening only one satelite window
					
		# start mode
		if 'Run' in self.DOptions and self.DOptions['Run'] in ['Yes', True]:
			self.Buttons['Run'].animateClick()
			
	
	def keyPressEvent(self, e):
		"""	recognizes shortcuts to show satelite windows (Genomes, Trajectories, Field, Legend, Film...)
		"""
		self.ParentClass.keyPressEvent(self,e)
		# Additional key actions
		try:
			if e.key() == QtCore.Qt.Key_G:  self.Buttons['Genomes'].animateClick()
			if e.key() == QtCore.Qt.Key_P:  self.Buttons['Photo'].animateClick()
			if e.key() == QtCore.Qt.Key_T:  self.Buttons['Trajectories'].animateClick()
			if e.key() == QtCore.Qt.Key_N:  self.Buttons['Network'].animateClick()
			if e.key() == QtCore.Qt.Key_F:  self.Buttons['Field'].animateClick()
			if e.key() == QtCore.Qt.Key_L:  self.Buttons['Log'].animateClick()		
			if e.key() == QtCore.Qt.Key_I:  self.Buttons['Image'].animateClick()		
			if e.key() == QtCore.Qt.Key_D:  self.Buttons['Legend'].animateClick()		
			if e.key() == QtCore.Qt.Key_V:  self.FilmButtonClick(e)
		except KeyError:	pass
		self.checkButtonState()

	def GenomeButtonClick(self, event):
		if 'Genomes' not in self.Buttons:	return
		if not 'Genomes' in self.SWindows:
			self.SWindows['Genomes'] = Evolife_Graphic.Genome_window(control=self,
																outputDir=self.Obs.get_info('OutputDir'), 
																image=self.Background['Genomes'], zoom=Screen_.ratio)
			# moving the window
			self.SWindows['Genomes'].move(*Screen_.locate(800, 200))		
			self.WindowActivation('Genomes')
		else:	self.SWindows['Genomes'].Raise()

	def PhotoButtonClick(self, event):
		"""	saves a snapshot of the simulation and goes to stepwise mode
		"""
		if 'Photo' not in self.Buttons:	return
		if self.PhotoMode:
			self.Obs.TextDisplay('Photo mode ended\n')
			self.PhotoMode = 0
		else:
			self.PhotoMode = 1  # take one shot
			self.StepButtonClick()
			self.Obs.TextDisplay('\nPhoto mode' + self.Obs.__str__() + '\n' + 'Frame %d' % self.CurrentFrame)
			if not self.Obs.Visible():	self.Process_graph_orders()	# possible if photo event occurs between years

	def FilmButtonClick(self, event):
		"""	Film mode is activated by pressing the 'V' key (video)
			It results in images (snapshots) being saved each time Observer is 'visible'
		"""
		if 'Photo' not in self.Buttons:	return
		# at present, the button is not shown and is only accessible by pressing 'V' 
		self.PhotoMode = 2 - self.PhotoMode
		if self.PhotoMode:
			self.setWindowTitle("%s (FILM MODE)" % self.Name)
		else:	self.setWindowTitle(self.Name)
	
	def TrajectoryButtonClick(self, event):
		"""	displays the 'Trajectories' window
		"""
		if 'Trajectories' not in self.Buttons:	return
		if 'Trajectories' not in self.SWindows:
			self.SWindows['Trajectories'] = Evolife_Graphic.Trajectory_window(control=self, 
												Wtitle='Trajectories', 
												outputDir=self.Obs.get_info('OutputDir'), 
												image=self.Background['Trajectories'], zoom=Screen_.ratio)
			# moving the window
			self.SWindows['Trajectories'].move(*Screen_.locate(275, 500))		
			self.WindowActivation('Trajectories')
		else:	self.SWindows['Trajectories'].Raise()
   
	def NetworkButtonClick(self, event):
		"""	displays the 'Network' window
		"""
		if 'Network' not in self.Buttons:	return
		if 'Network' not in self.SWindows:
			self.SWindows['Network'] = Evolife_Graphic.Network_window(control=self, 
												outputDir=self.Obs.get_info('OutputDir'), 
												image=self.Background['Network'], zoom=Screen_.ratio)
			self.WindowActivation('Network')
			self.SWindows['Network'].move(*Screen_.locate(790, 500))
		else:	self.SWindows['Network'].Raise()
	
	def FieldButtonClick(self, event):
		"""	displays the 'Field' window
		"""
		if 'Field' not in self.Buttons:	return
		if 'Field' not in self.SWindows:
			self.SWindows['Field'] = Evolife_Graphic.Field_window(control=self, 
												Wtitle=self.Name, 
												outputDir=self.Obs.get_info('OutputDir'), 
												image=self.Background['Field'], zoom=Screen_.ratio)
			# moving the window
			self.SWindows['Field'].move(*Screen_.locate(800, 100))		
			self.WindowActivation('Field')
		else:	self.SWindows['Field'].Raise()
		
	def LogButtonClick(self, event):
		"""	[not implemented]
		"""
		if 'Log' not in self.Buttons:	return
		self.Obs.TextDisplay('LogTerminal\n')
		pass			
	
	def WindowActivation(self, WindowName):		# complement after click
		"""	Sets Satellite window's geometry, icon and title
		"""
		self.SWindows[WindowName].setWindowIcon(QtGui.QIcon(os.path.join(self.Obs.get_info('EvolifeMainDir'),self.IconName)))
		self.Process_graph_orders()
		if WindowName in self.SWindowsPreferredGeometry:
			self.SWindows[WindowName].dimension(*self.SWindowsPreferredGeometry[WindowName])
		if WindowName in self.SWindowsMargins and self.SWindowsMargins[WindowName]:	
			self.SWindows[WindowName].Area.set_margins(*self.SWindowsMargins[WindowName])
		if WindowName in self.WindowTitles:	self.SWindows[WindowName].setWindowTitle(self.WindowTitles[WindowName])
		
	def checkButtonState(self):
		"""	sets the availability of the 'Network', 'Field', 'Image', 'Trajectories' tick button on display
		"""
		for B in self.Buttons:
			if B in ['Network', 'Field', 'Image', 'Trajectories', 'Log']:
				if self.Buttons[B].isEnabled and B not in self.SWindows:
					self.Buttons[B].setCheckState(False)
				if self.Buttons[B].isEnabled and B in self.SWindows:
					self.Buttons[B].setCheckState(True)
							 
	def Process_graph_orders(self):
		"""	Processes graph orders received from observer.
			Parent class displays PlotData by adding points to curves and by displaying them.
			In addition, gets orders for satelite windows from Oberver and processes them.
		"""
	
		ImgG, ImgN, ImgF, ImgT = ('',) * 4
		if 'Genomes' in self.SWindows:
			ImgG = self.SWindows['Genomes'].genome_display(genome=self.Obs.get_data('DNA'),
													gene_pattern=self.Obs.get_info('GenePattern'),
													Photo=self.PhotoMode, CurrentFrame=self.CurrentFrame)
		if 'Network' in self.SWindows:
			ImgN = self.SWindows['Network'].Network_display(self.Obs.get_data('Field', Consumption=False),
														self.Obs.get_data('Network'),
														Photo=self.PhotoMode, CurrentFrame=self.CurrentFrame)
		if 'Field' in self.SWindows:
			self.SWindows['Field'].image_display(self.Obs.get_info('Image'), windowResize=True)
			ImgF = self.SWindows['Field'].Field_display(self.Obs.get_data('Field'), 
												 Photo=self.PhotoMode,
												 CurrentFrame=self.CurrentFrame,
												 Ongoing=self.FieldOngoingDisplay, Prefix='___Field_')
		if 'Trajectories' in self.SWindows:
			self.SWindows['Trajectories'].image_display(self.Obs.get_info('Pattern'), windowResize=True)
			ImgT = self.SWindows['Trajectories'].Field_display(self.Obs.get_data('Trajectories'),
												  Photo=self.PhotoMode,
												  CurrentFrame=self.CurrentFrame, Ongoing=self.FieldOngoingDisplay, Prefix='___Traj_')
		if self.PhotoMode == 1:	
			if ''.join([ImgG, ImgN, ImgF, ImgT]):
				self.Obs.TextDisplay('%s Created' % ' '.join([ImgG, ImgN, ImgF, ImgT]))
		self.ParentClass.Process_graph_orders(self)  # draws curves (or not)
		self.checkButtonState()

	def DecisionToEnd(self):
		"""	Exits if 'ExitOnEnd' is True
		"""
		if 'ExitOnEnd' in self.DOptions and self.DOptions['ExitOnEnd'] in [True, 'Yes']:
			self.PhotoMode = 1	# taking photos
			self.Process_graph_orders()
			self.Buttons['Quit'].animateClick()	# exiting
		
	def SWDestroyed(self, SW):
		self.ParentClass.SWDestroyed(self,SW)
		self.checkButtonState()		
				
	def closeEvent(self, event):
		self.ParentClass.closeEvent(self, event)
		event.accept()


##################################################
# Creation of the graphic application			#
##################################################

def Start(SimulationStep, Obs, Capabilities='C', Options={}):
	""" SimulationStep is a function that performs a simulation step
		Obs is the observer that stores statistics
		Capabilities (curves, genome display, trajectory display...)
			= any string of letters from: CFGNTP
			C = Curves 
			F = Field (2D seasonal display) (excludes R)
			G = Genome display
			I = Image (same as Field, but no slider)
			L = Log Terminal
			N = social network display
			P = Photo (screenshot)
			R = Region (2D ongoing display) (excludes F)
			T = Trajectory display
		
		Options is a dict:
		- Run:True	means that the simulation will run automatically
		- Background:<Colour or image>
		- ExitOnEnd:True	doesn't pause when simulation stops
		
	"""

	MainApp = QtWidgets.QApplication(sys.argv)
	
	global Screen_
	Screen_ = Screen.Screen_(MainApp)	# stores physical dimensions of display
	Screen_.switchScreen()
	
	if set(Capabilities) <= set('CFGILNPRT'):
		# print(Evolife_Frame.__mro__)
		MainWindow = Evolife_Frame(SimulationStep, Obs, Capabilities, Options)
		  
		# Entering main loop
		MainApp.exec_()
		# if os.name != 'nt':	
		MainApp.deleteLater()	# Necessary to avoid problems on Unix
	else:
		MainWindow = None
		print("""   Error: <Capabilities> should be a string of letters taken from: 
		C = Curves 
		F = Field (2D seasonal display) (excludes R)
		G = Genome display
		I = Image (same as Field, but no slider)
		L = Log Terminal
		N = social network display
		P = Photo (screenshot)
		R = Region (2D ongoing display) (excludes F)
		T = Trajectory display
		""")


	
		
if __name__ == '__main__':

	print(__doc__)


__author__ = 'Dessalles'

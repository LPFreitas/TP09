#!/usr/bin/env python3

""" @brief  Windows that display Genomes, Labyrinth and Social networks for Evolife.
	
	Useful classes are:
	- Genome_window:  An image area that displays binary genomes
	- Network_window: A drawing area that displays social links
	- Field_window:   A drawing area that displays agent movements
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
#  Evolife_Graphic                                                           #
##############################################################################



import sys
if __name__ == '__main__':  sys.path.append('../..')  # for tests

try:	
	from PyQt5 import QtGui, QtCore, QtWidgets
	# grabWidget = QtGui.QScreen.grabWindow
	grabWidget = QtWidgets.QWidget.grab
except ImportError:				# compatibility with PyQt4
	from PyQt4 import QtGui, QtCore
	from PyQt4 import QtGui as QtWidgets
	grabWidget = QtGui.QPixmap.grabWidget

import os.path
import sys
from time import sleep
from math import ceil
sys.path.append('..')


from Evolife.Graphics.Plot_Area import Image_Area, Draw_Area, Ground
from Evolife.Tools.Tools import Nb2A0, warning


##################################################
# Structure of Events                            #
##################################################
class ViewEvent:
	"""	returned information after click 
	"""
	def __init__(self, EmittingClass, EventType, Info):
		self.EmittingClass = EmittingClass
		self.EventType = EventType
		self.Info = Info
	
	def __str__(self):
		return '%s/%s: %s' % (self.EmittingClass, self.EventType, str(self.Info))
		

##################################################
# Container window for drawing canvas            #
##################################################

class AreaView(QtWidgets.QGraphicsView):
	""" Standard canvas plus resizing capabilities
	"""
	def __init__(self, AreaType=Image_Area, parent=None, image=None, width=400, height=300, zoom=1):
		"""	Defining View: a window (QGraphicsView) that contains a plot area (QGraphicsScene)
		"""
		QtWidgets.QGraphicsView.__init__(self, parent)	  # calling the parent's constructor
		if AreaType:
			# View is a kind of camera on Area
			self.Area = AreaType(image, width=width, height=height, EventInterpreter=self.EventInterpreter, zoom=zoom)	 
			self.setScene(self.Area)
			self.resize(self.Area.W, self.Area.H)
		else:	error("AreaView", "No area to display")
		self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)	# necessary to avoir infinite loop with resizing events
		self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
		# self.setMinimumSize(180, 180)	# apparently necessary for PyQt5
		
	def paintEvent(self, e):
		"""	calls Qt's paintEvent
		"""
		QtWidgets.QGraphicsView.paintEvent(self,e)

	def resizeEvent(self,e):
		"""	calls Qt's resizeEvent
		"""
		if self.Area is not None:
			self.Area.resize(e.size().width(), e.size().height())
		QtWidgets.QGraphicsView.resizeEvent(self,e)

	def updateScene(self, L):
		"""	unused
		"""
		pass
	
	def photo(self, Name, FrameNumber=-1, outputDir='.', extension='png'):
		"""	takes a snapshot and saves it to a new file
		"""
		if FrameNumber >= 0:
			self.FrameNumber = FrameNumber
		else:
			self.FrameNumber += 1
		sleep(0.1)
		picture = grabWidget(self)
		ImFileName = Name + Nb2A0(self.FrameNumber)
		picture.save(os.path.join(outputDir, ImFileName + '.' + extension))
		return ImFileName
		
	def EventInterpreter(self, Event):
		"""	Does nothing here. To be overloaded
		"""
		# if Event[0] == 'MouseClick':	print(Event)
		pass


##################################################
# Basic keyboard control                         #
##################################################

class Active_Frame(AreaView):
	""" An Active_frame reacts to basic keyboard control
	"""
	def __init__(self, AreaType=None, parent=None, control=None, image=None, width=400, height=300, zoom=1):
		"""	Creates a window (AreaView) with the appropriate AreaType (Draw_Area, Ground...)
		"""
		if AreaType is not None:
			# calling the parents' constructor
			AreaView.__init__(self, AreaType=AreaType, parent=parent, image=image, 
								width=width, height=height, zoom=zoom)	
		else:
			# print(self.__class__.__mro__)
			QtWidgets.QWidget.__init__(self, parent=parent)
			# super(QtWidgets.QWidget, self).__init__()
			self.Area = None
		self.Parent = parent
		self.Control = control			  # memorizing who is in charge (buttons)
		if self.Control is None:
			self.control = self.Parent

	def keyPressEvent(self, e):	   
		"""	Definition of keyboard shortcuts
		"""
		if e.key() in [QtCore.Qt.Key_Q, QtCore.Qt.Key_Escape]:
			self.close()
		elif e.key() == QtCore.Qt.Key_M:
			self.Control.Raise()
			#self.Control.raise_()
			#self.Control.activateWindow()
		else:
			self.Control.keyPressEvent(e)

	def Raise(self):
		"""	puts the window on top of display
		"""
		self.raise_()
		self.activateWindow()

	def EventInterpreter(self, Event):
		if self.Control:
			self.Control.EventInterpreter(ViewEvent(type(self).__name__, Event[0], Event[1]))

##################################################
# Floating satellite window                      #
##################################################

class Satellite_window(Active_Frame):
	""" Satellite windows are floating windows with zooming abilities
	"""
	def __init__(self, AreaType=None, control=None, Wtitle='', image=None, width=400, height=300, zoom=1):
		"""	calls the parents' constructor with the appropriate area (QGraphicsScene) type
		"""
		Active_Frame.__init__(self, AreaType=AreaType, control=control, image=image, 
						width=width, height=height, zoom=zoom)	
		self.Title = Wtitle
		self.setWindowTitle(Wtitle)
		self.show()
		self.minSize = 8
		self.setMinimumSize(int(180*zoom), int(180*zoom))	# apparently necessary for PyQt5
		self.zoomingFactor = zoom
		self.Zoom(ZoomFactor=zoom)

	def dimension(self, *geometry):
		"""	sets dimensions
		"""
		if len(geometry) == 1:	
			width = int(geometry[0] * self.zoomingFactor)
			height = int(float(width)/self.Area.W * self.Area.H)
			posx, posy = 0,0
		else:
			geometry = list(geometry)	# [x,y,w,h] with optional x,y
			geometry.reverse()
			geometry += [0, 0][:4-len(geometry)]
			# height, width, posy, posx = list(map(lambda x: x * self.zoomingFactor, geometry))
			height, width, posy, posx = geometry
		if posx and posy:	self.setGeometry(posx, posy, width, height)
		else:	self.resize(width, height)	# used at initialization
		# return self.Area.dimension()
	
	def keyPressEvent(self, e):
		"""	adds resizing keys (+ and -) to Active_Frame's shortcuts
		"""
		Active_Frame.keyPressEvent(self,e)
		# Additional key actions
		if e.key() in [QtCore.Qt.Key_Z, QtCore.Qt.Key_Minus]:
			self.DeZoom()
		if e.key() in [QtCore.Qt.Key_Plus]:
			self.Zoom()

	def image_display(self, Image, windowResize=True):
		"""	display an image, with possible resizing of the window
		"""
		if Image is None or not os.path.exists(str(Image)):   return
		self.Area.Board = QtGui.QPixmap(Image) # loads the image
		if windowResize:
			# newWidth = self.Area.W
			newWidth = min(800, self.Area.Board.width())
			newHeight = min(600, self.Area.Board.height())
			try:	zoomFactor = min(float(newWidth) / self.Area.Board.width(), float(newHeight) / self.Area.Board.height())
			except	ZeroDivisionError:	zoomFactor = 1
			self.resize(int(self.Area.Board.width()*zoomFactor), int(self.Area.Board.height()*zoomFactor))
			self.Area.redraw()	
		else:	self.Area.redraw()
		self.setWindowTitle(self.Title + ' - ' + Image)

	def Zoom(self, ZoomFactor=1.1):
		"""	increase the window's size
		"""
		self.resize(int(self.width()*ZoomFactor),int(self.height()*ZoomFactor))

	def DeZoom(self, DeZoomFactor=0.91):
		"""	decrease the window's size
		"""
		self.resize(int(self.width()*DeZoomFactor),int(self.height()*DeZoomFactor))

	def closeEvent(self, event):
		"""	destroys the window
		"""
		if self.Control is not None:
			try:
				self.Control.SWDestroyed(self)  # should be done with a signal
			except Exception as Msg: print(Msg)
		event.accept()

##################################################
# Graphic area for displaying images			#
##################################################

class Image_window(Satellite_window):
	""" Image_window: Merely contains an image area
	"""
	def __init__(self, control=None, Wtitle='', outputDir='.'):
		"""	calls Satellite_window's constructor
		"""
		self.OutputDir = outputDir
		self.W = 300
		self.H = 200
		self.defaultSize = True   # will become false when we know genome size
		Satellite_window.__init__(self, Draw_Area, control=control, Wtitle='Images', width=self.W, height=self.H)
		self.Area.set_margins(1, 1, 1, 1)

		
##################################################
# Graphic area for displaying genomes			#
##################################################

class Genome_window(Satellite_window):
	""" Genome_window: An image area that displays binary genomes
	"""
	def __init__(self, control=None, image=None, genome=None, gene_pattern=None, outputDir='.', zoom=1):
		"""	calls Satellite_window's constructor
			and performs first display
		"""
		self.gene_pattern = gene_pattern
		self.OutputDir = outputDir
		self.H = 100
		self.W = 100
		self.defaultSize = True   # will become false when we know genome size
		if genome is not None:
			self.H = len(genome)
			self.W = len(genome[0])
			self.defaultSize = False
		Satellite_window.__init__(self, Draw_Area, control=control, Wtitle='Genomes', image=image, width=self.W, height=self.H, zoom=zoom)
		self.minSize = 100
		self.Area.set_margins(1, 1, 1, 1)
		if genome is not None:
			self.genome_display(genome=genome, gene_pattern=self.gene_pattern)
		self.Area.grid = self.axes

	def axes(self):
		"""	draws separation between genes
		"""
		if self.gene_pattern is None:	return
		gridPen = QtGui.QPen()
		gridPen.setColor(QtGui.QColor('#FF0000'))	# red lines to indicate gene limit
		gridPen.setWidth(1)
		pattern = list(self.gene_pattern)
		G = 1
		HPos = 0
		while G in pattern:
			# vertical lines
			HPos += (pattern.index(G) * self.Area.W)/self.W
			self.Area.addLine( self.Area.LeftMargin + HPos, self.Area.TopMargin,
						  self.Area.LeftMargin + HPos, self.Area.H - self.Area.BottomMargin, gridPen)
			del pattern[:pattern.index(G)]
			G = 1-G

	def genome_display(self, genome=None, gene_pattern=(), Photo=0, CurrentFrame=-1, Prefix=''):
		""" genome gives, for each individual, the sequence of binary nucleotides 
			gene_pattern is a binary flag to signal gene alternation
		"""
		
		PhotoName = ''
		if Photo:
			if Prefix == '':	Prefix = '___Genome_'
			PhotoName = self.photo(Prefix, CurrentFrame, outputDir=self.OutputDir)

		if genome is None or len(genome) == 0:  return ''
		if gene_pattern is not None:	self.gene_pattern = gene_pattern
		self.H = len(genome)
		self.W = len(genome[0])
		if self.defaultSize:
			self.resize(max(self.W, self.minSize), max(self.H, self.minSize))
			self.defaultSize = False

		#GenomeImg = QtGui.QImage(W,H,QtGui.QImage.Format_RGB32)	# why not this (?) format ?
		GenomeImg = QtGui.QImage(self.W, self.H, QtGui.QImage.Format_Mono)

		for line in range(self.H):
			for pixel in range(self.W):
				if genome[line][pixel]:
					GenomeImg.setPixel(pixel,line, 1)
				else:
					GenomeImg.setPixel(pixel,line, 0)
		# We should add the bitmap with window background. Don't know how to do this
		self.Area.Board = QtGui.QBitmap.fromImage(GenomeImg.scaled(self.Area.W,self.Area.H))
		self.Area.redraw()
		return PhotoName

									
##################################################
# A graphic area that displays social links	  #
##################################################

class Network_window(Satellite_window):
	""" Network_window: A drawing area that displays social links
		The population is displayed twice, on two horizontal axes.
		Social links are displayed as ascending vectors from one individual
		on the bottom line to another on the upper line.
	"""
	def __init__(self, control, image=None, outputDir='.', width=540, height=200, zoom=1):
		"""	calls Satellite_window's constructor
		"""
		Satellite_window.__init__(self, Draw_Area, control=control, Wtitle='Social network',
								  width=width, height=height, image=image, zoom=zoom)
		self.OutputDir = outputDir
		#self.Area.grid = self.axes
		# self.Area.Board.fill(QtGui.QColor(QtCore.Qt.white))
		self.Area.set_margins(20,20,20,20)
		self.axes()
		self.friends = {}


	def axes(self):
		""" Draws two horizontal axes; each axis represents the population;
			social links are shown as vectors going from the lower line
			to the upper one
		"""
		self.Area.move(6, (0, self.Area.scaleY))
		self.Area.plot(6, (self.Area.scaleX, self.Area.scaleY))
		self.Area.move(6, (0, 0))
		self.Area.plot(6, (self.Area.scaleX, 0))

	def Network_display(self, Layout, network=None, Photo=0, CurrentFrame=-1, Prefix=''):
		"""	Social links are displayed as ascending vectors from one individual
			on the bottom line to another on the upper line.
		"""
		PhotoName = ''
		if Photo:
			PhotoName = self.Dump_network(self.friends, CurrentFrame, Prefix=Prefix)

		# print(network)
		if not network:	return ''
		positions = dict([L for L in Layout if len(L) == 2 and type(L[1]) == tuple]) # positions of individuals
		if positions == {}:	return None
		self.friends = dict(network)
		self.Area.scaleX = max(self.Area.scaleX, max([positions[individual][0] for individual in positions]))
		self.Area.erase()
		self.axes()
		for individual in self.friends:
			if len(self.friends[individual]):
				bestFriend = self.friends[individual][0]
				self.Area.move(6, (positions[individual][0],0))
				try:
					self.Area.plot(6, (positions[bestFriend][0],self.Area.scaleY), 2)
				except KeyError:	warning('friend has vanished', bestFriend)
##				if len(self.friends[friend]) and individual == self.friends[friend][0]:
##					self.plot(6, (positions[friend][0],self.scaleY), 3)
##				else:
##					# changing thickness of asymmetrical links
##					self.plot(6, (positions[friend][0],self.scaleY), 1)
		return PhotoName

	def Dump_network(self, friends, CurrentFrame=-1, Prefix=''):
		"""	stores social links into a matrix written into a file
		"""
		if Prefix == '':	Prefix = '___Network_'
		PhotoName = self.photo(Prefix, CurrentFrame, outputDir=self.OutputDir)
		MatrixFileName = os.path.join(self.OutputDir, Prefix + Nb2A0(self.FrameNumber) + '.txt')
		MatrixFile = open(MatrixFileName,'w')
		for Individual in friends:
			MatrixFile.write(str(Individual))
			for F in friends[Individual]:
				MatrixFile.write('\t%s' % F)
			MatrixFile.write('\n')
		MatrixFile.close()
		return PhotoName


##################################################
# A graphic area that displays moving agents	 #
##################################################

class Field_window(Satellite_window):
	""" Field: A 2D widget that displays agent movements
	"""

	def __init__(self, control=None, Wtitle='', image=None, outputDir='.', width=400, height=300, zoom=1):
		if image:
			Satellite_window.__init__(self, Ground, control=control, Wtitle=Wtitle, image=image, zoom=zoom)
			self.image_display(image, windowResize=True)	# to resize
		else:
			Satellite_window.__init__(self, Ground, control=control, Wtitle=Wtitle, image=None, width=width, height=height, zoom=zoom)
		self.FreeScale = not self.Area.fitSize	# no physical rescaling has occurred - useful to shrink logical scale to acual data
		if self.FreeScale:
			self.Area.scaleX = 1.0 # virtual coordinates by default
			self.Area.scaleY = 1.0 # virtual coordinates by default
			# self.Area.redraw()	
		self.OutputDir = outputDir
		self.Area.grid()

	def Field_display(self, Layout=None, Photo=0, CurrentFrame=-1, Ongoing=False, Prefix=''):
		""" displays agents at indicated positions
			If Ongoing is false, agents that are not given positions are removed
			
			 Layout may come with two syntaxes:
				- ((Agent1Id, Coordinates1), (Agent2Id, Coordinates2), ...)
				- (Coordinates1, Coordinates2, ...)
			 The first format allows to move and erase agents
			 The second format is merely used to draw permanent blobs and lines
			 Coordinates have the following form:
				(x, y, colour, size, ToX, ToY, segmentColour, segmentThickness, 'shape=<form>')
				(shorter tuples are automatically continued with default values - 'shape=...' can be inserted anywhere)
			 The effect is that an object of size 'size' is drawn at location (x,y) (your coordinates, not pixels)
			 and a segment starting from that blob is drawn to (ToX, ToY) (if these values are given)
			 If you change the coordinates of an agent in the next call, it will be moved.
			 'size' is in pixels and is not resized in case of zoom. However, if negative, it is interpreted in your coordinates and it will be resized/
			 'size' may be a fractional number (float). It is then understood as a fraction of the window size.
			 The value assigned to 'shape' in the string 'shape=...' can be 'ellipse' (=default) or 'rectangle' or
			 any image. If it is an image, 'colour' is interpreted as an angle. The image is scaled to fit 'size' (but aspect ratio is preserved)
			
			 These two forms of vectors can be used to draw in two windows:  'Trajectories' and 'Field'.
			 Use the order:	record(vector, Window=<'Field'|'Trajectories'>)
			 or:				record([vectors], Window=<'Field'|'Trajectories'>)
			 'Field' is default. The latter order is used to send a list of vectors.
			
			 The 'Field' window comes in two modes, 'F' and 'R' (see option F and R at Evolife's start)
			 	- In the 'F' mode, all agents should be given positions at each call.
			 	  Missing agents are destroyed from display.
				- In the 'R'  ('Region') mode, you may indicates positions only for relevant agents
				  To destroy an agent from display, give a negative value to its colour.
		"""

		PhotoName = ''
		if Photo:
			if Prefix == '':	Prefix = '___Field_'
			PhotoName = self.photo(Prefix, CurrentFrame, outputDir=self.OutputDir)

		if not Layout:   return ''

		
		# separating agents from mere coordinates
		AgentLayout = dict([L for L in Layout if len(L) == 2 and type(L[1]) == tuple]) # positions of individuals
		DrawingLayout = [L for L in Layout if len(L) != 2 or type(L[1]) != tuple]
		
		# print(' '.join(AgentLayout.keys()))
		if DrawingLayout:
			if DrawingLayout == ['erase']:	
				self.erase()
			else:
				# adapting scale 
				if self.FreeScale:	self.adaptscale(DrawingLayout)
				# agent names are not given, Layout designates mere drawing instructions and not agents
				for Pos in DrawingLayout:
					# if Pos == 'erase':	self.erase()
					self.Area.draw_tailed_blob(Pos)
				
		if AgentLayout:
			# adapting scale at first call
			if self.FreeScale:	self.adaptscale(AgentLayout.values())
			# getting the list of agents already present
			# existing agents that are not redrawn are removed
			if not Ongoing:	self.Area.remove_absent(AgentLayout.keys())
			for Individual in AgentLayout:
				self.Area.move_agent(Individual, AgentLayout[Individual])
				# creates agent if not already existing
				

		# self.FreeScale = False
		
		return PhotoName

	def erase(self):
		"""	calls Area erase
		"""
		self.Area.erase()

	def adaptscale(self, Layout):
		"""	rescales widget if items land outside (only for max values, not for negative ones)
		"""
		newScaleX = max(self.Area.scaleX, max([pos[0] for pos in Layout]))
		newScaleY = max(self.Area.scaleY, max([pos[1] for pos in Layout]))
		if (newScaleX, newScaleY) != (self.Area.scaleX, self.Area.scaleY):
			self.Area.scaleX, self.Area.scaleY = ceil(newScaleX), ceil(newScaleY)
			# print(self.Title, self.Area.scaleX, self.Area.scaleY)
			self.Area.redraw()
			
	def Field_scroll(self):
		self.Area.scroll()

class Trajectory_window(Field_window):
	""" Synonymous for Field_window
	"""
	pass
		
		
class Help_window(QtWidgets.QTextBrowser):
	""" Displays a text file supposed to provide help
	"""
	def __init__(self, Control=None, Wtitle='Help'):
		"""	calls Qt's QTextBrowser
		"""
		QtWidgets.QTextBrowser.__init__(self)
		self.setWindowTitle(Wtitle)
		self.Control = Control

	def keyPressEvent(self, e):	   
		"""	Definition of keyboard shortcuts
		"""
		if e.key() in [QtCore.Qt.Key_Q, QtCore.Qt.Key_Escape]:
			self.close()
		elif e.key() == QtCore.Qt.Key_M:
			self.Control.Raise()
		else:
			self.Control.keyPressEvent(e)

	def display(self, HelpFilename):
		"""	show help window
		"""
		self.setPlainText(open(HelpFilename).read())
		self.setOverwriteMode(False)
		self.show()

	def Raise(self):
		"""	puts help widget in front of display
		"""
		self.raise_()
		self.activateWindow()

	def closeEvent(self, event):
		"""	destroys help widget
		"""
		if self.Control is not None:
			try:
				self.Control.SWDestroyed(self)  # should be done with a signal
			except Error as Msg:
				print(Msg)
		event.accept()

class Legend_window(Help_window):
	"""	displays legend for curves 
	"""
	def __init__(self, Control=None, Wtitle='Legend'):
		"""	legend window is copied from help window
		"""
		Help_window.__init__(self, Control=Control, Wtitle=Wtitle)
	
	def display(self, Legend, Comments=''):
		"""	Legend comes as a list of couples (ColourName, Meaning) 
		"""
		# self.setPlainText(Text + '\n\npress [Esc]')
		self.setOverwriteMode(False)
		
		# self.insertPlainText('\nCurves:')
		self.insertHtml('<P><u>Curves</u>:<br>')
		try:
			for (CID, Ccolour, Ccolourname, CName, CLegend) in Legend:
				# self.insertPlainText('\n')
				if CID == 2: # white colour, printed in black
					self.insertHtml('<br><b><font color="black">%s:</font></b>' % (Ccolour))
				else:
					self.insertHtml('<br><b><font color="%s">%s:</font></b>' % (Ccolour, Ccolourname))
				self.insertPlainText('\t')
				self.insertHtml('%s' % CLegend)
		except IndexError:
			error("Curves: unknown Curve ID")
			
		if Comments:	
			self.insertPlainText('\n')
			self.insertHtml('%s' % Comments)
		self.insertPlainText('\n=============\n( [Esc] to close )')

		# resizing window around text (from http://stackoverflow.com/questions/9506586/qtextedit-resize-to-fit )
		text = self.document().toPlainText()    # or another font if you change it
		font = self.document().defaultFont()    # or another font if you change it
		fontMetrics = QtGui.QFontMetrics(font)      # a QFontMetrics based on our font
		textSize = fontMetrics.size(0, text)
		textWidth = textSize.width() + 30       # constant may need to be tweaked
		textHeight = textSize.height() + 30     # constant may need to be tweaked
		self.setMinimumSize(textWidth, textHeight)  # good if you want to insert this into a layout
		# self.resize(textWidth, textHeight)          # good if you want this to be standalone		
		
		self.moveCursor(QtGui.QTextCursor.Start)
		self.ensureCursorVisible() ;

		
		
		# self.setTextColor(QColor(EvolifeColourID(Position.colour)[1]))
		self.show()

	
##################################################
# Local Test									 #
##################################################

if __name__ == "__main__":

	print(__doc__)


__author__ = 'Dessalles'

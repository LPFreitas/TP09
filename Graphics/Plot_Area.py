#!/usr/bin/env python3

""" @brief  Windows that display Curves or images.
	
	This module can be used independently.

	Useful classes are:
	- Image_Area:   An area that displays an image
		function:   display(<bitmap>)
	- Draw_Area:	Basic drawing Area
		function:   plot(<plot_number>, (<x>, <y>) )
	- Plot_Area:	Draw_Area + grid + automatic resizing
		function:   plot(<plot_number>, (<x>, <y>) )
	- Ground:	   Defines a 2-D region where agents are located and may move
		functions:  create_agent(<name>, <colour_number>, (<x>, <y>) )
					move_agent(<name>, (<Newx>, <Newy>) )

	Usage:
		#self.W = QPlot_Area.AreaView(QPlot_Area.Image_Area)
		self.W = QPlot_Area.AreaView(QPlot_Area.Draw_Area)
		#self.W = QPlot_Area.AreaView(QPlot_Area.Plot_Area)
		self.W.Area.plot(3,(10,10))
		self.W.Area.plot(3,(20,40))
		self.W.Area.plot(3,(10,22))
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
#  Plot Area                                                                 #
##############################################################################




import sys
if __name__ == '__main__':  sys.path.append('../..')  # for tests


import os
import random
from math import log
from time import sleep

try:	
	from PyQt5 import QtGui, QtCore, QtWidgets
	QString = lambda x: x
except ImportError:			# compatibility with PyQt4
	from PyQt4 import QtGui, QtCore
	from PyQt4 import QtGui as QtWidgets
	#	compatibility with python 2
	if sys.version_info >= (3,0):	QString = lambda x: x
	else:							QString = QtCore.QString


sys.path.append('..')

from Evolife.Graphics.Curves import Curves, Stroke, EvolifeColourID
from Evolife.Tools.Tools import error, Nb2A0

# scalar array multiplication
ZoomL = lambda *L: map(lambda x: int(x * L[0]), L[1:])	


##################################################
# Basic graphic area type                        #
##################################################

class Image_Area(QtWidgets.QGraphicsScene):
	""" Defines a logical Area on which objects are drawn (hidden from screen)
	"""

	def __init__(self, image=None, width=1000, height=1000, EventInterpreter=None, zoom=1):
		"""	Inherits from QGraphicsScene
		"""
		QtWidgets.QGraphicsScene.__init__(self, 0, 0, width, height)   # calling the parent's constructor
		if image is not None and os.path.exists(str(image)):
			#print "Loading %s . . ." % image
			self.ScaledBoard = self.Board = QtGui.QPixmap(image) # loads the image
			#error("Plot","Unable to find image %s" % image)
			self.fitSize = True
		else:
			# By default, a Scene has a graphic area (pixmap) on which one can draw
			self.ScaledBoard = self.Board = QtGui.QPixmap(width,height)
			image_ID = EvolifeColourID(image, default=None)
			if image_ID is not None:
				self.Board.fill(QtGui.QColor(image_ID[1]))
			elif image and image.startswith('#'):	# background colour given by code
				self.Board.fill(QtGui.QColor(image))
			else:	# default
				# self.Board.fill(QtGui.QColor("#F0B554"))
				self.Board.fill(QtGui.QColor("#FFFFFF"))
			self.fitSize = False
		self.Canvas = self.addPixmap(self.ScaledBoard)
		self.W = int(self.width())
		self.H = int(self.height())
		self.FrameNumber = 0
		self.EventInterpreter = EventInterpreter
		# self.changed.connect(self.Changing)
		self.zoom = zoom

	# # def Changing(self, e):
		# # print 'Changing', e
		
	def resize(self, w, h):
		"""	Stores new dimensions and redraws
		"""
		self.W = int(w)
		self.H = int(h)
		#self.ScaledBoard = self.Board.scaled(w, h)
		self.redraw()
		
	def dimension(): 
		"""	returns dimensions
		"""
		return (self.width(), self.height())

	def redraw(self):
		"""	the whole scene is redrawn when the scale changes
		"""
		for obj in self.items():
			self.removeItem(obj)
		self.ScaledBoard = self.Board.scaled(self.W, self.H)
		self.Canvas = self.addPixmap(self.ScaledBoard)
		self.setSceneRect(self.itemsBoundingRect())
		#self.setSceneRect(0, 0, self.W/10.0, self.H/10.0)
		
		
	def drawPoints(self):
		"""	Unused ------ just for test 
		"""
		item = QtGui.QGraphicsEllipseItem(20, 10, 40, 20, None, self)
		qp = QtGui.QPainter()
		qp.begin(self.Board)
		pen = QtGui.QPen()
		pen.setColor(QtCore.Qt.red)
		pen.setWidth(3)
		qp.setPen(pen)
		for i in range(10):
			x = random.randint(1, self.W-1)
			y = random.randint(1, self.H-1)
			qp.drawLine(0,0,x, y)	 
		qp.end()
		self.Canvas.setPixmap(self.ScaledBoard)


##################################################
# Graphic area with drawing capabilities		 #
##################################################

	
class Draw_Area(Image_Area, Curves):
	""" Draw_Area: Basic drawing Area
	"""
	
	def __init__(self, image=None, width=400, height=400, EventInterpreter=None, zoom=1):
		"""	Calls Image_Area constructor
			Initializes Curves
		"""
		Image_Area.__init__(self, image, width, height, EventInterpreter, zoom=zoom)
		self.set_margins(*ZoomL(zoom, 6, 6, 6, 6))
		self.OrigineX = 0
		self.OrigineY = 0
		if True:
		# if not self.fitSize:
			self.scaleX = 100.0	# current maximal horizontal value
			self.scaleY = 100.0	# current maximal vertical value
		# else:
			# self.scaleX = self.W
			# self.scaleY = self.H
		Curves.__init__(self)
		self.init_Pens()	# initializes pens for drawing curves

	def set_margins(self, Left, Right, Bottom, Top):
		"""	surrounding margins (in Image_Area pixels)
		"""
		self.LeftMargin = Left
		self.RightMargin = Right
		self.BottomMargin = Bottom
		self.TopMargin = Top
		
	def init_Pens(self):
		"""	Defining one pen and one QPainterPath per curve
		"""
		self.Pens = dict()
		##		self.PainterPaths = dict()   # polygons
		##		self.PainterPathRefs = dict()	# reference to polygons in the scene
		for Curve in self.Curves:
			self.Pens[Curve.ID] = QtGui.QPen()
			self.Pens[Curve.ID].setColor(QtGui.QColor(Curve.colour))
			self.Pens[Curve.ID].setWidth(3)
		##			self.PainterPaths[Curve.ID] = BoundedPath(QtCore.QPointF(self.convert((0,0))[0], self.convert((0,0))[1]))
		##			self.PainterPathRefs[Curve.ID] = self.addPath(self.PainterPaths[Curve.ID], self.Pens[Curve.ID])
				   
	def grid(self):
		"""	Initial display - to be overloaded
		"""
		pass

	def pixel2xy(self, Point):
		"""	converts physical coordinates into logical pixel(between 0 and scaleX)
		"""
		(px,py) = Point
		return (px * self.scaleX / (self.W - self.LeftMargin - self.RightMargin), 
				py * self.scaleY / (self.H - self.BottomMargin - self.TopMargin))
	
	def xy2pixel(self, Point):
		"""	converts logical pixel (between 0 and scaleX) into physical coordinates through rescaling 
		"""
		(x,y) = Point
		if self.scaleX and self.scaleY:
			return (((self.W - self.LeftMargin - self.RightMargin) * x) / self.scaleX,
					((self.H - self.BottomMargin - self.TopMargin) * y) / self.scaleY )
		return (0,0)
	
	def convert(self, Point):
		"""	Conversion of logical coordinates into physical coordinates through scaling and margin translation 
		"""
		(x,y) = self.xy2pixel(Point)
		return (self.LeftMargin + x, self.H - self.BottomMargin - y )

	def Q_Convert(self, Point):
		"""	Conversion of Point into Qt point
		"""
		(x,y) = self.convert(Point)
		#print "(%02f, %02f) converti en (%02f, %02f) avec scale=(%02f, %02f)" % (Point[0], Point[1], x ,y, self.scaleX, self.scaleY)
		return QtCore.QPointF(x, y)
	
	def draw(self, oldpoint, newpoint, Width=3, ColorID=0, Tag=''):
		"""	adds a segment on a given curve 
		"""
		##		self.PainterPaths[ColorID].moveTo(self.Q_Convert(oldpoint))
		##		self.drawTo(newpoint, Width, ColorID, Tag=Tag)
		if Width:
			# print('drawing from', oldpoint, 'to', newpoint, 'width', Width, 'with colour', ColorID)
			self.Pens[ColorID].setWidth(int(Width))
			self.addLine(QtCore.QLineF(self.Q_Convert(oldpoint), self.Q_Convert(newpoint)), self.Pens[ColorID])

	def drawTo(self, newpoint, Width=3, ColorID=0, Drawing=True, Tag=''):
		""" draws an additional segment on a given curve (from the end of the previous one)
		"""
		#print ">>>>>>>>", newpoint, self.Q_Convert(newpoint)
		##		if Drawing:	self.PainterPaths[ColorID].lineTo(self.Q_Convert(newpoint))
		##		else:	   self.PainterPaths[ColorID].moveTo(self.Q_Convert(newpoint))
		##		self.PainterPathRefs[ColorID].setPath(self.PainterPaths[ColorID])
		##		if self.PainterPaths[ColorID].full():
		##			self.PainterPaths[ColorID] = BoundedPath(self.PainterPaths[ColorID].currentPosition())
		##			self.PainterPathRefs[ColorID] = self.addPath(self.PainterPaths[ColorID], self.Pens[ColorID])
		self.draw(self.Curves[ColorID].last(), newpoint, Width, ColorID, Tag)

		
	def erase(self):
		"""	erase curves, items and restore grid
		"""
		for P in self.Curves:
			P.erase()
		for obj in self.items():
			if obj != self.Canvas:
				self.removeItem(obj)
		self.init_Pens()
		self.grid()
				
	def redraw(self):
		"""	the whole picture is redrawn when the scale changes
		"""
		Image_Area.redraw(self)
		self.init_Pens()
		self.grid()
		for Curve in self.Curves:
			for Segment in Curve:
				# print(Segment)
				self.draw(Segment[0], Segment[1], Width=Curve.thick, ColorID=Curve.ID)

	def reframe(self, Point, Anticipation=False):
		"""	performs a change of scale when necessary
		"""
		self.change = False
		def rescale(Scale, coord):
			# print(coord, Scale)
			if coord <= Scale:
				return Scale
			self.change = True
			if Anticipation:
				ordre = 10 ** (int(log(coord,10)))  # order of magnitude
				Scale = (coord // ordre + 1) * ordre
			else:
				Scale = coord
			return Scale

		if isinstance(Point, Stroke):	
			ws, hs = self.pixel2xy((Point.size, Point.size))
			# ws, hs = ((Point.size, Point.size))
			(x,y) = (Point.x + ws, Point.y + hs)
		else:	(x,y) = Point
		self.scaleX = rescale(self.scaleX, x)
		self.scaleY = rescale(self.scaleY, y)
		return self.change

	def plot(self, Curve_designation, newpoint, Width=3):
		"""	draws an additional segment on a curve
		"""
		# one is tolerant about the meaning of Curve_designation
		Curve_id = EvolifeColourID(Curve_designation)[0]
		# print('plotting to', Curve_designation, Curve_id, newpoint)
		try:
			# if Width != self.Curves[Curve_id].thick:	print('changing thickness of %s to %s' % (Curve_designation, Width))
			self.Curves[Curve_id].thick = Width		# update thickness
			self.drawTo(newpoint, Width, Curve_id)	# action on display
			self.CurveAddPoint(Curve_id, newpoint)		# memory
		except IndexError:
			error("Draw_Area: unknown Curve ID")

	def move(self, Curve_designation, newpoint):
		"""	introduces a discontinuity in a curve
		"""
		# one is tolerant about the meaning of Curve_designation
		Curve_id = EvolifeColourID(Curve_designation)[0]
		# print('moving to', Curve_designation, Curve_id, newpoint)
		try:
##			self.drawTo(newpoint, Curve_id, Drawing=False)
			self.CurveAddPoint(Curve_id, newpoint, Draw=False)
		except IndexError:
			error("Draw_Area: unknown Curve ID")
	
	def speck(self, Curve_id, newpoint, Size=3):
		"""	draws a spot 
		"""
		# print('about to draw speck at', Curve_id, newpoint)
		if self.reframe(newpoint):	self.redraw()
		self.move(Curve_id, newpoint)
		self.plot(Curve_id, newpoint, Width=Size)
	
	def mouseLocate(self, MouseEvent):
		"""	convert mouse position into window coordinates 
		"""
		mousePosition = MouseEvent.scenePos()
		x = mousePosition.x() - self.LeftMargin
		y = self.H - mousePosition.y() - self.BottomMargin
		if x >= 0 and y >= 0 and self.EventInterpreter:
			return self.pixel2xy((x,y))
		return None
		
	def mousePressEvent(self, MouseEvent):
		"""	retrieves mouse clicks - added by Gauthier Tallec 
		"""
		Loc = self.mouseLocate(MouseEvent)
		if Loc is not None:
			self.EventInterpreter(('MouseClick', Loc))

	def mouseReleaseEvent(self, MouseEvent):
		"""	retrieves mouse clicks 
		"""
		Loc = self.mouseLocate(MouseEvent)
		if Loc is not None:
			self.EventInterpreter(('MouseDeClick', Loc))

	def mouseDoubleClickEvent(self, MouseEvent):
		"""	retrieves mouse clicks 
		"""
		Loc = self.mouseLocate(MouseEvent)
		if Loc is not None:
			self.EventInterpreter(('MouseDoubleClick', Loc))

	def mouseMoveEvent(self, MouseEvent):
		"""	retrieves mouse movements when button is pressed 
		"""
		Loc = self.mouseLocate(MouseEvent)
		if Loc is not None:
			self.EventInterpreter(('MouseMove', Loc))


		
##################################################
# Graphic area for displaying curves			 #
##################################################
	
class Plot_Area(Draw_Area):
	""" Definition of the drawing area, with grid, legend and curves
	"""
	def __init__(self, image=None, width=556, height=390, EventInterpreter=None, zoom=1):
		"""	Calls Draw_Area constructor and sets margins 
		"""
		Draw_Area.__init__(self, image, width, height, EventInterpreter, zoom=zoom)
		self.set_margins(*ZoomL(zoom, 32, 20, 28, 20))
		#self.grid()	 # drawing the grid
		self.init_Pens()	# redo it because offsets have changed
		
	def grid(self):
		"""	Drawing a grid with axes and legend  
		"""
		NbMailles = 5
		mailleX = (int(self.zoom * 0.5) + self.W - self.RightMargin - self.LeftMargin)/NbMailles
		mailleY = (int(self.zoom * 0.5) + self.H - self.TopMargin - self.BottomMargin)/NbMailles
		GridColour = '#A64910'
		gridPen = QtGui.QPen()
		gridPen.setColor(QtGui.QColor(GridColour))
		gridPen.setWidth(int(self.zoom))
		# drawing the grid
		for i in range(NbMailles+1): 
			# vertical lines 
			self.addLine( self.LeftMargin + i*mailleX, self.TopMargin,
								self.LeftMargin + i*mailleX, self.H - self.BottomMargin, gridPen)
			# horizontal lines
			self.addLine( self.LeftMargin, self.TopMargin + i*mailleY,
								self.W - self.RightMargin, self.TopMargin + i*mailleY, gridPen)
		# drawing axes
		gridPen.setWidth(int(self.zoom * 2))
		self.addRect(self.LeftMargin,self.TopMargin,self.W-self.RightMargin+1-self.LeftMargin,
					 self.H-self.BottomMargin+1-self.TopMargin, gridPen)

		# drawing legend
		PSize = int((13 - 2 * int(log(max(self.scaleX, self.scaleY), 10))))		# size of police
		for i in range(NbMailles+1):
			# legend on the x-axis
			self.addSimpleText(QString(str(int(i*self.scaleX//NbMailles)).center(3)),
						QtGui.QFont(QString("Arial"), PSize)).setPos(QtCore.QPointF(self.LeftMargin+i*mailleX-int(self.zoom*12), 
									self.H-self.BottomMargin+int(self.zoom*5)))
			# legend on the y-axis
			self.addSimpleText(QString(str(int(i*self.scaleY//NbMailles)).rjust(3)),
						QtGui.QFont(QString("Arial"), PSize)).setPos(QtCore.QPointF(self.LeftMargin-int(self.zoom*25), 
								self.H - self.BottomMargin - i*mailleY-6))

		# drawing colour code
		for C in self.Curves[1:]:
			self.addEllipse(self.W - self.RightMargin/2, self.H - C.ID * self.BottomMargin/2 - int(self.zoom*20),
							  int(self.zoom*4),int(self.zoom*4),
							  QtGui.QPen(QtGui.QColor(C.colour)), QtGui.QBrush(QtGui.QColor(C.colour), QtCore.Qt.SolidPattern))

			

	def plot(self, Curve_id, newpoint, Width=3):
		""" A version of PLOT that checks whether the new segment
			remains within the frame. If not, the scale is changed
			and all curves are replotted
		"""
		if self.reframe(newpoint, Anticipation=True):
			self.redraw()
		Draw_Area.plot(self, Curve_id, newpoint, Width=Width)


##################################################
# 2-D Graphic area for displaying moving agents  #
##################################################
class Ground(Draw_Area):
	""" Defines a 2-D region where agents are located and may move
	"""

	DEFAULTSHAPE = 'ellipse'
	# DEFAULTSHAPE = 'rectangle'

	def __init__(self, image=None, width=400, height=300, legend=True, EventInterpreter=None, zoom=1):
		"""	Creates a Draw_Area and initializes agents
		"""
		self.Legend = legend and (image == None or EvolifeColourID(image)[0])	# no image or uniform color
		self.Toric = False  # says whether right (resp. top) edge
							# is supposed to touch left (resp. bottom) edge
		Draw_Area.__init__(self, image, width, height, EventInterpreter, zoom=zoom)
		self.set_margins(*ZoomL(zoom, 6, 6, 6, 6))
		#self.Board.fill(QtGui.QColor(QtCore.Qt.white))
		self.Canvas.setPixmap(self.ScaledBoard)
		self.positions = dict() # positions of agents
		self.segments = dict()	# line segments pointing out from agents
		self.shapes = dict()	# shape of agents
		self.GraphicAgents = dict()	# Q-references of agents 
		self.KnownShapes = {}
			
	def setToric(self, Toric=True):
		"""	if toric, edges 'touch' each other
		"""
		self.Toric = Toric
		
	def grid(self):
		"""	Writing maximal values for both axes 
		"""
		if self.Legend:
			self.addSimpleText(QString(str(round(self.scaleY))),
						QtGui.QFont(QString("Arial"), 8)).setPos(QtCore.QPointF(self.LeftMargin + int(self.zoom*3),
																   int(self.zoom*7) + self.TopMargin))
			self.addSimpleText(QString(str(round(self.scaleX))),
						QtGui.QFont(QString("Arial"), 8)).setPos(QtCore.QPointF(self.W - self.RightMargin-int(self.zoom*16) ,
																   self.H-self.BottomMargin - int(self.zoom*8)))

	def coordinates(self, Coord):
		"""	Coord is a tuple.
			It has the following form:
			(x, y, colour, size, ToX, ToY, segmentColour, segmentThickness, 'shape=<form>')
			(shorter tuples are automatically continued with default values - 'shape=...' can be inserted anywhere)
			The effect is that an object of size 'size' is drawn at location (x,y) (your coordinates, not pixels)
			and a segment starting from that blob is drawn to (ToX, ToY) (if these values are given)
			# 'size' is in pixels and is not resized in case of zoom. However, if negative, it is interpreted in your coordinates and it will be resized/
			# 'size' may be a fractional number. It is then understood as a fraction of the window size.
			# The value assigned to 'shape' in the string 'shape=...' can be 'ellipse' (=default) or 'rectangle' or
			# any image. If it is an image, 'colour' is interpreted as an angle. The image is scaled to fit 'size' (but aspect ratio is preserved)
		"""

		Shape = None
		# shape is indicated anywhere as a string
		Coord1 = tuple()
		for x in Coord:
			if type(x) == str and x.lower().startswith('shape'):	Shape = x[x.rfind('=')+1:].strip()
			else:	Coord1 += (x,)
		Start = Stroke(Coord1[:4], RefSize=self.W)
		if len(Coord1) > 4:	End = Stroke(Coord1[4:], RefSize=self.W)
		else:	End = Stroke(None)	# no segment
		return (Start, End, Shape)
				
	def convert(self, Coord):
		"""	process modulo if toric and calls Draw_Area's convert
		"""
		if self.Toric:
			Coord = (Coord[0] % self.scaleX, Coord[1] % self.scaleY)
		return Draw_Area.convert(self, Coord)
								 
	def create_agent(self, Name, Coord):
		""" creates a dot at some location that represents an agent 
		"""
		self.move_agent(Name, Coord)	# move_agent checks for agent's existence and possibly creates it
		
	def move_agent(self, Name, Coord=None, Position=None, Segment=None, Shape=None):
		""" moves an agent's representative dot to some new location 
		"""	  
		def physical_move(AgentRef, Location):
			"""	moves a shape to a location 
		"""
		# We want the origin of a shape to be the lower left corner (contrary to Qt convention)
			AgentRef.setPos(QtCore.QPointF(Location[0],Location[1]))	# performing actual move
			
		# Coord in analysed as a Position + an optional segment starting from that position, 
		# and missing coordinates are completed
		if Coord:	(Position, Segment, Shape) = self.coordinates(Coord)
		else:	Coord = Position.point() + Segment.point() + (('shape=%s' % Shape,) if Shape else ())
		Location = self.convert(Position.point()) # Translation into physical coordinates
		# if not self.Toric and self.reframe(Position):   # The window is reframed if necessary
			# self.redraw()	# poses display problems...
		if Name in self.positions:  	
			# print('moving', Name, 'in', Position.Coord, len(self.positions))
			if self.positions[Name].colour != Position.colour or self.shapes.get(Name) != Shape:
				# Colour or shape has changed, the agent is destroyed and reborn
				# print('Changing colour or shape')
				self.remove_agent(Name)
				if str(Position.colour).startswith('-'):
					# print('destroying agent', Name)
					return  # negative colour means the agent is removed
				self.move_agent(Name, Coord)	# false recursive call
			if self.positions[Name].Coord == Position.Coord \
					and self.segments[Name].Coord == Segment.Coord \
					and self.shapes.get(Name) == Shape:
				return  # nothing to do
			#### moving an existing agent ####
			# print Name, Position.Coord,  self.positions[Name].Coord
			self.positions[Name] = Position	# recording the agent's new position
			self.shapes[Name] = Shape	# recording the agent's new shape
			AgentRef = self.GraphicAgents[Name][0]
			# AgentRef.setPos(QtCore.QPointF(Location[0],Location[1]))	# performing actual move
			physical_move(AgentRef, Location)
			if self.segments[Name].Coord:	# the segment is re-created
				self.remove_segment(Name)
			if Segment.Coord:
				SegmentRef = self.create_graphic_segment(Position, Segment)
			else:	SegmentRef = None
			self.segments[Name] = Segment
			self.GraphicAgents[Name] = (AgentRef, SegmentRef)	# New Q-reference to graphic objects are memorized
		else:   #### creating the agent ####
			# print('creating', Name, 'in', Position.Coord, len(self.positions))
			try:
				if str(Position.colour).startswith('-'):
					# print 'Error negative colour in display -->\t\t', Position.Coord
					return
				AgentRef = self.create_graphic_agent(Position, Shape)	# creating the shape or loading the image
				# AgentRef.setPos(QtCore.QPointF(Location[0],Location[1]))		# translating the shape or image
				physical_move(AgentRef, Location)
				if Segment.Coord:
					# drawing the segment that originates from the shape
					SegmentRef = self.create_graphic_segment(Position, Segment)
				else:	SegmentRef = None
			except IndexError:
				error("Draw_Area: unknown colour ID")
			self.positions[Name] = Position	# recording the agent's new position
			self.shapes[Name] = Shape	# recording the agent's new shape
			self.segments[Name] = Segment
			self.GraphicAgents[Name] = (AgentRef, SegmentRef)	# Q-reference to graphic objects are memorized

	def create_graphic_agent(self, Position, Shape=None):
		"""	creates a graphic agent and returns the Q-reference 
		"""
		if Shape is None: Shape = self.DEFAULTSHAPE
		if Position.PixelSize:
			PhysicalW = PhysicalH = Position.size	# sizes are provided in pixels
		else:
			PhysicalW, PhysicalH = self.xy2pixel((Position.size, Position.size))	# sizes are provided in logical coordinates and are resized
		if Shape == 'ellipse':
			return self.addEllipse(0, -PhysicalH, PhysicalW, PhysicalH,
								   QtGui.QPen(QtGui.QColor(EvolifeColourID(Position.colour)[1])),
								 QtGui.QBrush(QtGui.QColor(EvolifeColourID(Position.colour)[1]), QtCore.Qt.SolidPattern))
		if Shape == 'rectangle':
			return self.addRect(0, -PhysicalH, PhysicalW, PhysicalH,
								   QtGui.QPen(QtGui.QColor(EvolifeColourID(Position.colour)[1])),
								 QtGui.QBrush(QtGui.QColor(EvolifeColourID(Position.colour)[1]), QtCore.Qt.SolidPattern))
		if Shape not in self.KnownShapes:
			if os.path.exists(Shape):
				# print('Existing shape: %s' % Shape)
				self.KnownShapes[Shape] = QtGui.QPixmap(Shape) # loads the image
		if Shape in self.KnownShapes:	# no else
			# interpreting colour as angle
			if Position.colour and type(Position.colour) == int:
				agent = self.addPixmap(self.KnownShapes[Shape].transformed(QtGui.QTransform().rotate(-Position.colour)))
			else:
				agent = self.addPixmap(self.KnownShapes[Shape])
			# currentSize, h = self.pixel2xy((agent.boundingRect().width(), 0))
			scaleW = float(PhysicalW) / agent.boundingRect().width()
			scaleH = float(PhysicalH) / agent.boundingRect().width()	# to keep aspect ratio
			agent.setTransform(QtGui.QTransform.fromScale(scaleW, scaleH))	# should be translated as well
			return agent
		error("Ground: unknown shape: %s" % Shape)
		return None

	def create_graphic_segment(self, Position, Segment):
		"""	creates a graphic segment and returns the Q-reference 
		"""
		Colour = EvolifeColourID(Segment.colour)[0]
		self.Pens[Colour].setWidth(Segment.size)
		Location1 = self.convert(Position.point())	# Translation into physical coordinates
		Location2 = self.convert(Segment.point())	# Translation into physical coordinates
		return self.addLine(Location1[0], Location1[1], Location2[0], Location2[1], self.Pens[Colour])
							 
	def remove_agent(self, Name):
		""" removes an agent from the ground
		"""
		self.remove_segment(Name)
		self.removeItem(self.GraphicAgents[Name][0])
		del self.positions[Name]
		del self.GraphicAgents[Name]

	def remove_segment(self, Name):
		"""	removes a segment from the ground
		"""
		if self.segments[Name].Coord:
			self.removeItem(self.GraphicAgents[Name][1])
		del self.segments[Name]
		
	def on_ground(self):
		"""	Returns the identificiation of all agents on the ground 
		"""
		return self.GraphicAgents.keys()

	def remove_absent(self, Present):
		"""	removes agents that are not in Present 
		"""
		for Name in list(self.GraphicAgents.keys()):	# ground copy of keys
			if Name not in Present:	self.remove_agent(Name)
		
	def scroll(self):
		"""	move agents vertically (not yet used)
		"""
		for Name in list(self.GraphicAgents.keys()):
			self.positions[Name].scroll()
			self.move_agent(Name, Position + Segment)	# addition has been  redefined

	def draw_tailed_blob(self, Coord):
		"""	draws a blob and a segment, as for an agent, 
			but without agent name and without moving and removing options 
		"""
		(Position, Segment, Shape) = self.coordinates(Coord)	
		# print(Position)
		# print(Segment)
		if not self.Toric and self.reframe(Position):   # The window is reframed if necessary
			self.redraw()
		if Segment.Coord:
			if Segment.size:
				self.move(Segment.colour, Position.point())
				self.plot(Segment.colour, Segment.point(), Width=Segment.size)
			else:	# invisible line
				self.move(Segment.colour, Segment.point())
				self.speck(Segment.colour, Segment.point(), Size=0)	# drawing invisible point to rescale
		self.speck(Position.colour, Position.point(), Size=Position.size)
	
	def erase(self):
		"""	removes agents and erases Draw_Area
		"""
		for Agent in list(self.GraphicAgents.keys()):	# copy because modified by restore_agent	
			self.remove_agent(Agent)
		Draw_Area.erase(self)	# modif 211105
		# self.redraw()	# modif 211105
		
	def redraw(self):
		"""	the whole picture is redrawn when the scale changes 
		"""
		# First, delete all unnamed objects (named objects are agents)
		Draw_Area.redraw(self)  # destroys all agents in the scene
		for Agent in list(self.GraphicAgents.keys()):	# copy because modified by restore_agent	
			if Agent in self.positions:  	# the agent is already displayed (and not in the process of being displayed)
				self.restore_agent(Agent)

	def restore_agent(self, Name):
		"""	display an agent that is still present in 'positions' and in 'segments', but is graphically dead 
		"""
		self.move_agent(Name, Position=self.positions.pop(Name), Segment=self.segments.pop(Name), 
				Shape=self.shapes.get(Name))
		
		
	
##################################################
# Local Test									 #
##################################################

if __name__ == "__main__":

	print(__doc__)


__author__ = 'Dessalles'

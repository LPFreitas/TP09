#!/usr/bin/env python3

""" @brief   Physical display (Screen and monitors).                                """

#============================================================================#
# EVOLIFE  http://evolife.telecom-paris.fr             Jean-Louis Dessalles  #
# Telecom Paris  2023-11-19                                www.dessalles.fr  #
# -------------------------------------------------------------------------- #
# License:  Creative Commons BY-NC-SA                                        #
#============================================================================#
# Documentation: https://evolife.telecom-paris.fr/Classes                    #
#============================================================================#

##############################################################################
##############################################################################

try:	from PyQt5 import QtWidgets
except ImportError:				# compatibility with PyQt4
		from PyQt4 import QtGui as QtWidgets

class Screen_:
	"""	Stores characteristics of physical display 
	"""
	
	def __init__(self, MainApp):
		"""	Stores available physical screens
		"""
		self.width = 1920	# will be changed
		self.height = 1080	# will be changed
		self.ratio = 1		# comparison with default screen
		screen_rect = MainApp.desktop().screenGeometry()
		self.ratio = screen_rect.width() / self.width
		self.width, self.height = screen_rect.width(), screen_rect.height()
		self.displays = []
		for Disp in range(0,8):
			D = QtWidgets.QDesktopWidget().screenGeometry(Disp)
			if D:	self.displays.append(D)
			else:	break
		self.currentScreen = 0
		# print(self.displays)
		
	def resize(self, *Coord):
		"""	applies screen's display ratio to coordinates
		"""
		return list(map(lambda x: int(x * self.ratio), Coord))
		
	def locate(self, *Coord):
		"""	calls 'resize' (for high definition screen and optional screen change)
		"""
		return self.changeScreen(list(self.resize(*Coord)))
	
	def switchScreen(self):
		"""	Chave the value of 'currentScreen'
		"""
		self.currentScreen = len(self.displays) - self.currentScreen - 1
	
	def changeScreen(self, Coord):
		"""	translates coordinates to display on current screen
		"""
		# print('Change coordinates:', Coord, end=' ')
		Coord = [Coord[0] + self.displays[self.currentScreen].left(), 
				 Coord[1] + self.displays[self.currentScreen].top()] \
				 + Coord[2:]
		# print('to ', Coord)
		return Coord
		
__author__ = 'Dessalles'

#!/usr/bin/env python3

""" @brief  Selection of relevant columns and lines in a numerical matrix
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
#  Result matrix analysis - New version                                      #
##############################################################################

#################################################################
# Selection of relevant columns and lines in a numerical matrix #
#################################################################

import sys
import re
import os
import getopt
import copy
import numpy as np

DELIMITER = ';'
# DELIMITER = ','
CONSTANTTHRESHOLD = 0.99	# fraction of majority value for column to be considered almost constant
ALMOSTCONSTANTTHRESHOLD = 0.8	# fraction of majority value for column to be considered almost constant
# STDDEVCONSTANTTHRESHOLD = 0.0001	# standard deviation threshold for a column to be considered constant
STDDEVVARIABLETHRESHOLD = 1	# standard deviation threshold for a column to be considered variable



def usage(command, Ext1='', Ext2='', Ext3='', Ext4='', verbose=False):
	Msg = f""" \nUsage:
	
{command} [-h] -r <ResultFile.csv> [-x <x-parameter>][-y <y-parameter>
		-z <z-data>] [-p <imposed parameter>[=<value>]]*
		[-d <imposed data>]*
		"""
	if verbose:	Msg += f"""
		
The programme eliminates constant columns in <ResultFile.csv>
(output: <ResultFile>{Ext1}); then stores data corresponding to <x-parameter>
values (output: <ResultFile>{Ext2}), taking majority values for non-imposed
parameters; then stores average values for each <x-parameter> value
(output: <ResultFile>{Ext3}).
If <y-parameter> is present, the programme computes average values
of <z-data> for each (x-parameter, y-parameter) couple
(output: <ResultFile>{Ext4}).
Option "-d" can be used to force the program to consider <imposed data> 
as a relevant column (and not as a fixed parameter). Useful when a
dimension does not vary much.


Note: the elimination of constant columns can be made once only:
	First launch:  {command} -r <ResultFile.csv>
	then launch {command} <ResultFile>{Ext1} ...
	as often as wanted with various x- and y- parameters.
	"""
	else:	Msg += f"\nFor more:	{command} -h\n"

	print(Msg)


def Histo(v):
	values = sorted(list(set(v)))
	H = np.histogram(v, bins = values + [v.max()+1])
	return sorted(zip(H[0], values), reverse=True)
	

def Majority(v):
	"""	returns the majority value in the vector
	"""
	return Histo(v)[0]



class ExpMatrix:
	""" Contains experiment results
		Each line: results of one experiment
	"""

	Default_Title = ['Evolife','Evolution of communication','www.dessalles.fr/Evolife']
	
	def __init__(self, InputMatrix=None, Names=[], FileName=''):
		# Header = open(FileName).readline().strip().split(DELIMITER)
		# first look to get aound genfromtxt bug
		if InputMatrix is None:
			Data = np.genfromtxt(FileName, delimiter=DELIMITER, skip_header=0, names=True, filling_values=0)
			self.Names = list(Data.dtype.names)
			# genfromtxt is unable to build genuine 2D array when names is True
			self.Matrix = np.array(list(map(np.array, zip(*Data))))
		else:
			self.Matrix = copy.deepcopy(InputMatrix)
			self.Names = Names[:]
		
		self.RelevantColumns = []
		self.Parameters = []
		self.DataColumns = []
		self.Majorities = dict()
		
	def ColIndex(self, ColName):
		return self.Names.index(ColName)
	
	def Copy(self):
		return ExpMatrix(InputMatrix=self.Matrix, Names=self.Names) 
		
	def RemoveColumns(self, ColNames):
		" Creates a new matrix without the column "

		OutputMatrix = self.Copy()
		for ColName in ColNames:
			ColIndex = OutputMatrix.ColIndex(ColName)
			OutputMatrix.Names.remove(ColName)
			OutputMatrix.Matrix = np.delete(OutputMatrix.Matrix, ColIndex, 0)
		
		return OutputMatrix
		
	def ColumnAnalysis(self, Parameter='', DataCol=[], ColumnFiltering=True, verbose=True):
		"""	Determines whether columns correspond to parameters, to variables or are constant
		"""

		def AlmostConstant(v, Threshold):
			# almost constant if a certain fraction of the values are the same
			return Majority(v)[0] > len(v) * Threshold

		def Variation(v):
			# if std < STDDEVCONSTANTTHRESHOLD:	return 'Constant'
			if AlmostConstant(v, CONSTANTTHRESHOLD):	return 'Constant'
			if AlmostConstant(v, ALMOSTCONSTANTTHRESHOLD):	return 'Almost constant'
			std = np.std(v)
			if std > STDDEVVARIABLETHRESHOLD:	return 'Highly variable'
			return 'Slightly variable'
		
		Columns = dict(zip(self.Names, self.Matrix))
		
		variations = {c:Variation(Columns[c]) for c in Columns}
		# print({c:np.std(Columns[c]) for c in Columns})
		print(variations)
		
		self.Majorities = { c:Majority(Columns[c])[1] for c in Columns }
		
		self.RelevantColumns = [c for c in variations if variations[c] != 'Constant']
		
		# List of columns which are likely parameters, i.e. have a fixed majority part and a variable part
		self.Parameters = [c for c in self.RelevantColumns if variations[c] == 'Almost constant']
		# forcing Parameter among Parameters
		if Parameter != '':
			self.RelevantColumns = list(set(self.RelevantColumns + [Parameter]))
			self.Parameters = list(set(self.Parameters + [Parameter]))
		if verbose:
			print("Parameters:\n\t%s" % ('\n\t'.join(self.Parameters)))
		
		# List of columns which are likely to contain data: those are highly variable
		DataColumns = set(self.RelevantColumns) - set(self.Parameters)

		# Keeping the original order
		self.DataColumns = [DC for DC in self.Names if DC in DataColumns]
		if verbose:
			print("Data columns:\n\t%s" % ('\n\t'.join(self.DataColumns)))

		
	def selectRelevantColumns(self, Parameter='', DataCol=[], ColumnFiltering=True, verbose=True):
		""" Eliminates constant or almost constant columns
		"""
		if verbose:
			print('Eliminating constant columns . . .')
			
		self.ColumnAnalysis(Parameter, DataCol, ColumnFiltering=ColumnFiltering, verbose=verbose)

		# selecting relevant columns while keeping original order
		ToBeRemoved = [C for C in self.Names if C not in self.RelevantColumns]
		# ToBeRemoved.append('Date')
		return self.RemoveColumns(ToBeRemoved)

	def selectRelevantLines(self, X_parameter='', Y_parameter='',
							SideParametersAndValues=[], DataCol=[], verbose=True):
		""" Suppresses lines in which non-relevant parameters vary
			and then columns corresponding to non-relevant parameters
			which are now constant
		"""
		if verbose:
			print('Selecting relevant lines . . .')
			
		if (X_parameter and X_parameter not in self.Names) \
		   or (Y_parameter and Y_parameter not in self.Names):
			print('Available columns: %s' % str(self.Names))
			print("**********ERROR: missing parameters: %s   %s" % (X_parameter, Y_parameter))
			# return [self.Names] + self.Lines
			return []

		# updates parameters (columns, etc.)
		self.ColumnAnalysis(Parameter=X_parameter, DataCol=DataCol, verbose=False) 
		# print(self.Majorities)
		

		# SideParameters are imposed parameters, with imposed value
		SideParameters = dict(SideParametersAndValues)
		
		# Columns which are likely parameters, i.e. have a fixed majority part and a variable part
		UsefulParameters = (set(self.Parameters) | set(SideParameters.keys())) \
							- set([X_parameter, Y_parameter] + DataCol)
							
		# displaying the majority column for each parameter
		for UP in UsefulParameters:
			try:	self.Majorities[UP]
			except KeyError:
				print('please check parameter spelling: %s %s %s' % (X_parameter,Y_parameter, ' '.join(list(SideParameters.keys()))))
				print('. . . Bye')
				sys.exit()
		if verbose:
			print('Detected parameters:')
			if X_parameter:
				print('\t%s (Relevant parameter)' % X_parameter)
			print('\n\t'.join(["%s (majority or chosen value: %s)" % (M, self.Majorities[M])
						 for M in SideParameters]))

		# print(UsefulParameters)
		# print([self.Majorities[UP] for UP in UsefulParameters])
		SelectedLines = []
		Lines = np.transpose(self.Matrix)
		for Line in Lines:
			Keep = True
			for UP in UsefulParameters:
				if Line[self.ColIndex(UP)] != self.Majorities[UP]:
					Keep = False
					break
				Keep = True
			if Keep:
				SelectedLines.append(Line)

		# sorting lines according to relevant parameters
		if X_parameter and Y_parameter:
			SelectedLines.sort(key=lambda x: (float(x[self.ColIndex(X_parameter)]),
											  float(x[self.ColIndex(Y_parameter)])))
		elif X_parameter:
			SelectedLines.sort(key=lambda x: (float(x[self.ColIndex(X_parameter)])))
							   
		return ExpMatrix(InputMatrix=np.array(np.transpose(SelectedLines)), Names=self.Names)
	
	def Export(self, FileName):
		np.savetxt(	FileName, np.transpose(self.Matrix), fmt='%s', delimiter=DELIMITER, 
					header=';'.join(self.Names), comments='', encoding='utf-8')
		print('------- %s has been created' % FileName)

	def __len__(self):	return len(self.Matrix)
	
	
class Histogram(ExpMatrix):
	""" Computes an histogram from another matrix
	"""

	def __init__(self, Matrix, X_parameter='', DataCol=[]):
		super().__init__(InputMatrix=Matrix.Matrix, Names=Matrix.Names)
		# If the first column is 'Date' it should be ignored
		# updating parameters
		self.ColumnAnalysis(Parameter=X_parameter, DataCol=DataCol, ColumnFiltering=False, verbose=False)
		self.x_parameter = X_parameter
		if self.x_parameter == '':
			self.x_parameter = self.Names[0]
		self.x_values = []
		self.Histogram = [[[]]] 

	def ComputeHistogram(self):
		""" Stores y-values sharing same x-values into lists for each data column
		"""
		self.x_index = self.ColIndex(self.x_parameter)
		self.x_values = sorted(list(set(self.Matrix[self.x_index])))
		# self.Histogram = np.zeros(shape=(len(self.Names), len(self.x_values)))
		Histogram = []
		# print(Histogram)
		# print(Matrix.shape)
		# print(Histogram.shape)
	
		Lines = np.transpose(self.Matrix)
		print(f'Computing histogram over {self.x_parameter}')
		# print(Lines[:4])
		for x_val in self.x_values:
			print(x_val, end='\t')
			x_indices = np.where(self.Matrix[self.x_index] == x_val)
			print(x_indices)
			x_lines = np.take(Lines, x_indices, axis=0)[0]
			print(x_lines)
			Histogram.append(np.mean(x_lines, axis=0))
		print()
		Histogram = np.array(Histogram)
		print(Histogram)
		print(Histogram.shape)
		return ExpMatrix(InputMatrix=np.transpose(Histogram), Names=self.Names)

	'''
	def ComputeAvg(self):
		# Mins =  [ [str(min(Col)) for Col in Histogram[val]] for val in range(len(Values))]   
		# Maxs =  [ [str(max(Col)) for Col in Histogram[val]] for val in range(len(Values))]   
##        self.Lines = [ [str(self.x_values[val])] + ["%2.2f" % ((1.0*sum(Col))/len(Col))
##                      for Col in self.Histogram[val]]
##                      for val in range(len(self.x_values))]
		self.Lines = []
		for x_i in range(len(self.x_values)):
			line = [str(self.x_values[x_i])]
			for Col in self.Histogram[x_i]:
				if len(Col):
					line.append("%2.2f" % ((1.0*sum(Col))/len(Col)))
				else:
					line.append("-1")
			self.Lines.append(line)
		self.Names = [self.x_parameter] + self.DataMatrix.DataColumns
	'''

class TwoDHistogram(Histogram):
	""" build a matrix from an x-parameter, a y-parameter and a z-data
		containing average results
	"""

	def __init__(self, Matrix, X_parameter, Y_parameter, Z_data, DataCol=[]):
		Histogram.__init__(self, Matrix=Matrix, X_parameter=X_parameter, DataCol=DataCol)
		self.Titles = ExpMatrix.Default_Title \
					  + [X_parameter, Y_parameter, Z_data] \
					  + self.Titles[len(ExpMatrix.Default_Title):]
		self.y_parameter = Y_parameter
		self.y_values = []
		self.z_data = Z_data

	def Compute2DHistogram(self):
		""" Stores z-values sharing same x-values and y-values into lists
		"""
		self.x_values = list(self.DataMatrix.Columns[self.x_parameter].values)
		self.y_values = list(self.DataMatrix.Columns[self.y_parameter].values)
		print(self.x_values)
		print(self.y_values)
		input()
		self.Histogram = [[[] for y in self.y_values] for x in self.x_values]
		self.hitp = []   # number of values for each (x_value,y_value) couple
		Cx = self.DataMatrix.ColIndex(self.x_parameter)
		Cy = self.DataMatrix.ColIndex(self.y_parameter)
		Cz = self.DataMatrix.ColIndex(self.z_data)

		print('Computing 2D-histogram of %s over %s and %s' \
			  % (self.z_data, self.x_parameter, self.y_parameter))
		for x_i in range(len(self.x_values)):
			x_val = self.x_values[x_i]
			print("\n%s\t" % str(x_val), end='')
			for y_j in range(len(self.y_values)):
				y_val = self.y_values[y_j]
				count = 0
				for line in self.DataMatrix.Lines:
					if		    line[Cx] == x_val \
							and line[Cy] == y_val:
						count += 1
						self.Histogram[x_i][y_j].append(float(line[Cz]))
				self.hitp.append((x_val,y_val,count))
				print('%s:%d' % (y_val,count), end='')
		print()

	def ComputeAvg(self):
		Histogram.ComputeAvg(self)
		self.Names = ["%s x %s" % (self.x_parameter, self.y_parameter)] \
					 + self.y_values

	def Representativity(self):
		self.hitp = [p for p in self.hitp if float(p[0]) <= 100 and float(p[1]) <= 100]
		self.hitp.sort(key=lambda x: x[2])
		return self.hitp




def CommandLine(Commandline):

	(ResultFileName, x_parameter, y_parameter, z_Data, SideParameters, SideData) = ('', '', '', '', [], [])

	# Command line analysis
	Options = getopt.getopt(Commandline, 'r:x:y:z:p:d:h')
	if Options[1]:
		raise Exception('surplus argument')
	for (O,A) in Options[0]:
		if O == '-r':
			ResultFileName = A
		if O == '-x':
			x_parameter = A
		if O == '-y':
			y_parameter = A
		if O == '-z':
			z_Data = A
		if O == '-p':
			ParamAndValue = A.strip('"').split('=')
			if len(ParamAndValue) == 2:
				SideParameters.append(tuple(ParamAndValue))
			elif len(ParamAndValue) == 1:
				SideParameters.append((ParamAndValue[0],None))			  
		if O == '-d':
			SideData.append(A)
		if O == '-h':
			raise ValueError('Help')
	if ResultFileName == '':
		raise ValueError('Absent file name')
	if y_parameter and not z_Data:
		raise ValueError('Need z_data when y_data is present')
	return (ResultFileName, x_parameter, y_parameter, z_Data, SideParameters, SideData)


def main():

	ConstantColRemovedFileExt = '_col.csv'
	SelectedLinesFileExt = '_lines.csv'
	HistogramFileExt = '_Histo.csv'
	TwoDHistogramFileExt = '_2DHisto.csv'

	try:
		(ResultFileName, x_parameter, y_parameter, z_Data, SideParameters, SideData) = CommandLine(sys.argv[1:])
	except getopt.GetoptError as err:
		usage(os.path.basename(sys.argv[0]), verbose=False)

		print("erreur dans les options : %s " % err)
		print('. . . Bye')
		sys.exit(2)
	except Exception as err:
		if str(err) == 'Help':
			usage(os.path.basename(sys.argv[0]),ConstantColRemovedFileExt,
				  SelectedLinesFileExt,HistogramFileExt,TwoDHistogramFileExt, verbose=True)
		else:
			usage(os.path.basename(sys.argv[0]), verbose=False)
			if str(err):	print('Error: %s' % err)
		print('. . . Bye')
		sys.exit(1)

		
	FileNameRoot = os.path.splitext(ResultFileName)[0]
	if ResultFileName.lower().endswith(ConstantColRemovedFileExt):
		# First step (suppression of constant columns) has already been performed
		FileNameRoot = re.split(ConstantColRemovedFileExt, ResultFileName)[0]
		ConstantColRemovedFileName = ResultFileName
	else:
		ConstantColRemovedFileName = FileNameRoot + ConstantColRemovedFileExt
	SelectedLinesFileName = FileNameRoot + SelectedLinesFileExt
	HistogramFileName = FileNameRoot + HistogramFileExt
	TwoDHistogramFileName = FileNameRoot + TwoDHistogramFileExt
	print(ResultFileName, FileNameRoot, ConstantColRemovedFileName, SelectedLinesFileName, HistogramFileName)

	# processing
	try:
		# retrieve result matrix from file
		RMatrix = ExpMatrix(FileName=ResultFileName)
		if ResultFileName != ConstantColRemovedFileName:
			# starting from raw material - Constant columns have to be removed
			AbridgedMatrix = RMatrix.selectRelevantColumns(x_parameter)
			AbridgedMatrix.Export(ConstantColRemovedFileName)
		else:
			print('Assuming %s is purged from constant columns' % ConstantColRemovedFileName)
			# hoping that x_parameter hasn't changed - The user knows what she's doing
			AbridgedMatrix = RMatrix
	except Exception as err:
##        from sys import excepthook, exc_info
##        excepthook(exc_info()[0],exc_info()[1],exc_info()[2])
		print(err)
		print('Mais tout va bien...')
		# raise(err)
		sys.exit()

	if x_parameter == '':
		print('Nothing more to do (missing x-parameter)')
		return

	SelectedLines = AbridgedMatrix.selectRelevantLines(X_parameter=x_parameter,
													   SideParametersAndValues=SideParameters,
													   DataCol=SideData)
	if len(SelectedLines) > 0:
		print('Eliminating new constant columns . . .')
		SelectedColumnsInSelectedLines = SelectedLines.selectRelevantColumns(x_parameter,
													   DataCol=SideData, ColumnFiltering=False, verbose=True)
		SelectedColumnsInSelectedLines.Export(SelectedLinesFileName)
		
		
		print('Building an histogram . . .')
		if 'Date' in SelectedColumnsInSelectedLines.Names:
			SelectedColumnsInSelectedLines = SelectedColumnsInSelectedLines.RemoveColumns(['Date'])
		H = Histogram(Matrix=SelectedColumnsInSelectedLines, X_parameter=x_parameter, DataCol=SideData)
		H.ComputeHistogram().Export(HistogramFileName)
	else:
		print("No lines left in the matrix")

	if y_parameter == '':
		return
	SelectedLines = AbridgedMatrix.selectRelevantLines(X_parameter=x_parameter,
													   Y_parameter=y_parameter,
													   SideParametersAndValues=SideParameters,
													   DataCol=SideData, verbose=False)
	if SelectedLines.Height > 0:
		SelectedColumnsInSelectedLines = SelectedLines.selectRelevantColumns(x_parameter,
													   DataCol=SideData, verbose=False)
		print('Building a 2D-histogram . . .')
		HH = TwoDHistogram(SelectedColumnsInSelectedLines , x_parameter, y_parameter, z_Data, DataCol=SideData)
		HH.Compute2DHistogram()
		HH.ComputeAvg()
		HH.Export(TwoDHistogramFileName)
		print('Least representative points:')
		print(HH.Representativity()[0:8])

if __name__ == "__main__":

	main()
	print('. . . Done')


__author__ = 'Dessalles'

#!/usr/bin/env python3

""" @brief  Global constants and parameters.
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
#  Global definitions                                                        #
##############################################################################


import sys
import re

if __name__ == '__main__':  sys.path.append('../..')  # for tests

from Evolife.Tools.Tools import FileAnalysis, error


#########################################
# Loding global parameters             #
#########################################

# a function to check whether a string represents a positive or negative integer
isInZ = lambda x: x.isdigit() or (len(x)>1 and x[0]=='-' and x[1:].isdigit())

def Num(x):	
	"""	interpreting numerical values 
	"""
	if type(x) == str:
		try:	return int(x)
		except ValueError:	return float(x)
	else:	return x

def Alph(x):
	"""	interpreting strings as possible python expressions 
	"""
	try:	return(eval(x))
	except (NameError, SyntaxError):	return x.strip()

def AlphNum(x):	
	"""	interpreting values 
	"""
	try:	return Num(x)
	except ValueError:	return Alph(x)

	
class Parameters(dict):
	""" class Parameters: stores all modifiable parameters
	"""

	def __init__(self, CfgFile='Evolife.evo', ParamDict=None):
		"""	Loads parameters from text file
		"""
		if ParamDict is not None:	dict.__init__(self, ParamDict)	# dictionnary of (parameter name, value)
		else:			dict.__init__(self, self.txt_to_cfg(CfgFile))
		self.Params = self	# backward compatibility
		self.relevant = set()  # list of parameters that are actually used
		for p in self:	self[p] = AlphNum(self.Parameter(p, Silent=True))
		# print(self)

	def __getitem__(self, ParamName):	
		# to make sure that 'relevant' will be processed
		return self.Parameter(ParamName)
	
	def txt_to_cfg(self,CfgTxtFile):
		""" retrieves a configuration from a text file
		"""
		try:
			# reads lines with following syntax:
			# [<Prefix/>*]<NameOfParameter> <ParameterValue> [<comments>]
			# Numerical parameters
			Numerical = FileAnalysis(CfgTxtFile, r"^(?:[^#][^\s,;]*/)?(\w+)[\s,;](-?\d+(?:\.\d*)?)\s*")	
			# # # # Numerical = [(V[1], Num(V[2])) for V in Numerical]
			# NonNumerical parameters
			# Alphabcal = FileAnalysis(CfgTxtFile, "^([^#][^\s,;]*/)?(\w+)[\s,;]+([^-0-9/]\S*).*$")	
			# Alphabcal = FileAnalysis(CfgTxtFile, "^(?:[^#][^\s,;]*/)?(\w+)[\s,;]+([^#\n]+)\s*$")	
			# Alphabcal = FileAnalysis(CfgTxtFile, r"^(?:[^#][^\s,;]*/)?(\w+)[\s,;](\S*)")	
			Alphabcal = FileAnalysis(CfgTxtFile, r"^(?:[^#][^\s,;]*/)?(\w+)[\s,;]+([^#\r\n]+)")
			# # # # Alphabcal = [(V[1],Alph(V[2])) for V in Alphabcal if not set(V[2]) <= set('-0123456789.') ]
			#cfg = {V[1]:int(V[2]) for V in R}
			cfg = dict(Numerical + Alphabcal)
##			if len(cfg) < len(Numerical + Alphabcal):
##				error("Evolife_Parameters: duplicated parameter", str([V for V in Numerical + Alphabcal if V not in cfg]))
			return cfg
		except IOError:
			error("Evolife_Parameters: Problem accessing configuration file", CfgTxtFile)
		return None

	def cfg_to_txt(self, CfgTxtFile):
		""" stores parameters into a text file
		"""
		Filout = open(CfgTxtFile, "w")
		Filout.write('\n'.join([p + '\t' + str(self[p])
								for p in sorted(self.relevant)]))
		Filout.close()
		
	def Parameter(self, ParamName, Silent=False, Default='dummy'):
		"""	Retrieves a parameter value.
			If Silent is False, ParamName is added to the list of relevant values.
		"""
		if Default != 'dummy':	p = self.get(ParamName, Default)
		else:
			try:	p = dict.__getitem__(self, ParamName)	# parent getitem
			except KeyError:	
				print(self.relevant)
				error("Evolife_Parameters: Attempt to reach undefined parameter: ", ParamName)
		if not Silent and ParamName not in self.relevant and ParamName in self: 
			self.relevant.add(ParamName)
		return p

	def Param(self, ParamName, default=None):
		"""	Retrieves a parameter value.
		"""
		if default is not None:	return self.Parameter(ParamName, Default=default) 
		return self[ParamName]
	
	def addParameter(self, Param, Value):
		"""	Adds a new parameter or modify its value
		"""
		self[Param] = Value
		
	def ParamNames(self):	
		"""	List of numerical parameters
		"""
		return [P for P in self if isInZ(str(self[P]))]

	def RelevantParamNames(self):	
		"""	List of relevant (i.e. used) parameters
		"""
		return sorted(self.relevant)

	def ParamValues(self):
		return self.values()

	def Relevant(self, ParamName):	
		"""	Checks whether a parameter is relevant (i.e. used)
		"""
		return ParamName in self.relevant

	def __str__(self):
		return '\n'.join(sorted([k+' =\t'+str(self[k]) for k in self]))




#################################
# Loading global parameters	 #
#################################

##Evolife_Parameters = Parameters('Evolife.evo')


	
	
if __name__ == "__main__":
	print(__doc__ + '\n')
	# print Defs.__doc__ + '\n'
	if len(sys.argv) > 1:
		Evolife_Parameters = Parameters(sys.argv[1])
	else:
		Evolife_Parameters = Parameters('../Evolife_.evo')
	print(Evolife_Parameters)
	input('\n[Return]')


__author__ = 'Dessalles'

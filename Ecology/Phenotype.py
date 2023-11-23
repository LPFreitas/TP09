#!/usr/bin/env python3

""" @brief  Definition of phenotype as non inheritable characters.
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
#  Phenotype                                                                     #
##############################################################################


import sys
if __name__ == '__main__':  sys.path.append('../..')  # for tests



import random
from Evolife.Tools.Tools import error



class Phene:
	"""	class Phene: define a non-heritable characteristics 
	"""
	MaxPheneValue = 100

	def __init__(self, Name, FlagRandom=True):
		"""	creates a zero-valued or a random characteristics, depending on FlagRandom 
		"""
		self.Name = Name
		if FlagRandom:
			self.__value = random.randint(0, Phene.MaxPheneValue)
		else:
			self.__value = 0

	def relative_value(self):
		"""	returns the Phene's value between 0 and 100 
		"""
		return (100.0 * self.__value) / Phene.MaxPheneValue

	def value(self, Value=None, Levelling = False):
		"""	sets or merely reads the Phene's value, possibly by limiting it to MaxPheneValue 
		"""
		if Value is None:	return self.__value
		if Value <= Phene.MaxPheneValue:	self.__value = Value
		elif Levelling:	self.__value = Phene.MaxPheneValue
		else:	error("Phenotype: ", "Maximum value exceeded: %f" % Value)
		return self.__value

	def __str__(self):
		return self.Name + '=' + "%d" % self.value()
	
class Phenome:
	"""	class Phenome: set of non inheritable characteristics 
	"""
	def __init__(self, Scenario, FlagRandom = True):
		"""	creates a dictionary of Phenes as defined by Scenario.phenemap() 
		"""
		self.Scenario = Scenario
		self.Phenes = {PN:Phene(PN,FlagRandom)
							for PN in self.Scenario.phenemap()}

	def Phene_value(self, name, Value=None, Levelling=False):
		"""	reads or sets the value of a phene 
		"""
		return self.Phenes[name].value(Value, Levelling)

	def Phene_relative_value(self, name):
		"""	returns a Phene's value between 0 and 100 
		"""
		return self.Phenes[name].relative_value()
	
	def signature(self):
		"""	returns phene values as a list of relative values 
		"""
		return [self.Phenes[PN].relative_value() for PN in self.Scenario.phenemap()]
				
	def __str__(self):
		return 'Phenotype:\n ' + ' <> '.join([Ph.__str__() for Ph in self.Phenes.values()])




if __name__ == "__main__":
	print(__doc__)
	from Evolife.Scenarii.MyScenario import InstantiateScenario
	InstantiateScenario('Signalling')
	from Evolife.Scenarii.MyScenario import MyScenario
	Ph = Phenome(FlagRandom = True)
	print(Ph)
	raw_input('[Return]')


__author__ = 'Dessalles'

#!/usr/bin/env python3

""" @brief 	 Removes CR chars introduced by MsWindows
"""


#============================================================================#
# EVOLIFE  http://evolife.telecom-paris.fr             Jean-Louis Dessalles  #
# Telecom Paris  2023-11-19                                www.dessalles.fr  #
# -------------------------------------------------------------------------- #
# License:  Creative Commons BY-NC-SA                                        #
#============================================================================#
# Documentation: https://evolife.telecom-paris.fr/Classes                    #
#============================================================================#

import sys
import os.path

sys.path.append('Tools')

import Walk

if __name__ == '__main__':
	print(__doc__)
	print("Do you want to remove all CR in python source files")
	if input('? ').lower().startswith('y'):
		# Walk.Browse('.', print, '.*.pyw?$', Verbose=False)
		Walk.SubstituteInTree('.', '.*.pyw?$', '\\r', '', Verbose=False)
		print('Done')
	else:
		print ('Nothing done')

__author__ = 'Dessalles'

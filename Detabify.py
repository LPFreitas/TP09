#!/usr/bin/env python3

""" @brief 	 Replaces tabs by chars in python files
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
import time

sys.path.append('Tools')

import Walk

if __name__ == '__main__':
	print(__doc__)
	# print("Do you want to replace all tabs by spaces in python source files")
	# if raw_input('? ').lower().startswith('y'):
	if True:
		# Detabify
		Walk.SubstituteInTree('.', '.*.py$', '\\t', ' '*4, CommentLineChars='#')
		# ReTabify
		# Walk.SubstituteInTree('.', '.*.py$', ' '*4, '\\t', CommentLineChars='#')
		print('Done')
	else:
		print('Nothing done')

__author__ = 'Dessalles'

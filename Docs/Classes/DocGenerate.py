#!/usr/bin/env python3

""" @brief  Generates doc from DocStrings """

#============================================================================#
# EVOLIFE  http://evolife.telecom-paris.fr             Jean-Louis Dessalles  #
# Telecom Paris  2023-11-19                                www.dessalles.fr  #
# -------------------------------------------------------------------------- #
# License:  Creative Commons BY-NC-SA                                        #
#============================================================================#
# Documentation: https://evolife.telecom-paris.fr/Classes                    #
#============================================================================#



##############################################################################
#  Documentation generation                                                  #
##############################################################################

import os
import glob
import re
import Walk
import DocGeneration

EvolifeDir = 'e:/recherch/Evolife'
# AvoidDirectories = [
	# # '___.*',
	# # 'Docs',
	# # 'Examples',
	# # 'Expe',
	# # 'Other',
	# 'Averaging.py',
	# 'EvolifeGray.py',
	# 'GenomeDisplay.py',
	# 'GifMaker.py',
	# 'Histogram.py',
	# ]
EvolifeSubDirectories = [
	'Ecology',
	'Genetics',
	'Graphics',
	'#Other',
	'Scenarii',
	'Social',
	# 'Tools',
	]
IsolatedFiles = [
	'Tools/Tools.py',
	]
Images = {
	'Group':'Evolife_Ecology.svg',
	'Observer':'Evolife_Observer.svg',
	'Curves':'Evolife_Graphics.svg',
	'Evolife_Window':'Evolife_Window.svg',
	'Default_Scenario':'Evolife_Scenario.svg',
}

HEADER = """
	%h2(%l+https://evolife.telecom-paris.fr(Evolife) documentation)


	%large+2(%s(right)) %l+Classes.html(summary)
	<hr/><p>	<p>
"""
FOOTER = """
	<hr/><p>	<p>
	%large(%l+https://evolife.telecom-paris.fr(Back to Evolife))
"""

def extractClasses(xjlfilename):
	" extrait les classes d'un fichier de documentation au format xjl "
	Content = open(xjlfilename).read()
	return re.findall(r'Class <span[^>]+>([^< ]+)', Content)
	

if __name__ == '__main__':
	print(__doc__)
	
	# fabrication des fichiers de documentation .xjl
	# lancer ensuite la commande xjl2html.bat
	
	for D in EvolifeSubDirectories:
		Walk.Browse(os.path.join(EvolifeDir, D), 
					lambda f: DocGeneration.DocGen(f, root=EvolifeDir, header=HEADER, footer=FOOTER), 
					SelectFilter='.*.py$', 
					AvoidFilter=['__.*', 'S_.*'], Verbose=False)
	for F in IsolatedFiles:
		DocGeneration.DocGen(os.path.join(EvolifeDir, F), root=EvolifeDir, header=HEADER, footer=FOOTER)
	
	# DocGeneration.DocGen(os.path.join(EvolifeDir, 'Main.py'))

	# fabrication du sommaire
	xjlList = glob.glob('Evolife*.xjl')
	SummaryString = '\n'.join(HEADER.split('\n')[:3])
	SummaryString += '%h3(List of Evolife classes)'
	SummaryString += '<hr/><p>	<p>'
	
	for xjlFile in sorted(xjlList):
		Module = os.path.splitext(xjlFile)[0]
		ModuleBasename = Module.split('.')[-1]
		if ModuleBasename in Images:
			SummaryString += f'%ir+30%(../Images/{Images[ModuleBasename]})'
		SummaryString += f'%h4(<a href="{Module}.html">{Module}</a>)%list\n'
		for Class in extractClasses(xjlFile):
			SummaryString += f'\t<a href="{Module}.html#{Class}">{Class}</a>\n'
	SummaryString += FOOTER
	open('Classes.xjl', 'w').write(SummaryString)
	print('Summary written in Classes.xjl')
	
	
__author__ = 'Dessalles'

#!/usr/bin/env python3

""" @brief  Definition of genes as DNA segment having semantics. """

#============================================================================#
# EVOLIFE  http://evolife.telecom-paris.fr             Jean-Louis Dessalles  #
# Telecom Paris  2023-11-19                                www.dessalles.fr  #
# -------------------------------------------------------------------------- #
# License:  Creative Commons BY-NC-SA                                        #
#============================================================================#
# Documentation: https://evolife.telecom-paris.fr/Classes                    #
#============================================================================#


##############################################################################
#  Genetic Map                                                                     #
##############################################################################



import sys
if __name__ == '__main__':  sys.path.append('../..')  # for tests


from Evolife.Tools.Tools import error

class Gene_def:
	"""	definition of semantic segments on DNA.
		A gene is a geographical entity: start_position, end_position, length... 
	"""

	def __init__(self, gene_name, gene_length, locus, position, coding):
		""" A gene knows its name, its length,
			its locus (order in the list of genes) and its start and end position
			on the DNA
		"""
		self.name = gene_name
		self.length = gene_length
		if self.length == 0:	error('Gene definition','Zero length with zero Default length')
		self.locus = locus					# rank in the list of genes
		self.start = position				# start location on DNA
		self.end = position + self.length	# end location on DNA
		self.coding = coding
		if self.coding in range(-1,3):
			# old numeric designation of coding
			self.coding = ['Nocoding', 'Weighted', 'Unweighted', 'Gray'][self.coding+1]		
		

	def __str__(self):
		return 'L' + str(self.locus) + ': ' + self.name + ' ' + str(self.start) + '->' + str(self.end) + ' '

class Genetic_map:
	"""	a Genetic_map is a series of genes, located one after the other 
	"""
	def __init__(self, GeneMap):
		"""	just calls init_genes 
		"""
		self.init_genes(GeneMap)

	def init_genes(self,gene_list):
		""" creates genes and puts them into 'GeneMap'
		Accepted syntax:
		['genename1', 'genename2',...]:   lengths and coding are retrieved from configuration.
		[('genename1', 8), ('genename2', 4),...]:   numbers give lengths in bits; coding is retrieved from configuration.
		[('genename1', 8, 'Weighted'), ('genename2', 4, 'Unweighted'),...]:	coding can be 'Weighted', 'Unweighted', 'Gray', 'NoCoding'.
		Note that 'Unweighted' is unsuitable to explore large space.		
		"""
		self.GeneMap = []
		locus = 0
		current_pos = 0
		# for (g_name,g_length) in gene_list:
		for GeneDefinition in gene_list:
			# genes are assigned locus and future position on DNA
			g_length = self.Parameter('GeneLength', Default=0)	# default value
			g_coding = self.Parameter('GeneCoding')	# default value
			if isinstance(GeneDefinition, tuple):
				if len(GeneDefinition) == 2:
					(g_name,g_length) = GeneDefinition
				elif len(GeneDefinition) == 3:
					(g_name,g_length, g_coding) = GeneDefinition
				else:	error("Bad definition of gene map")
			else:	g_name = GeneDefinition
			if g_length == 0:	g_length = self.Parameter('GeneLength')	# compatibility
			NewGene = Gene_def(g_name, g_length, locus, current_pos, g_coding)
			self.GeneMap.append(NewGene)
			locus += 1
			current_pos = NewGene.end

	def get_gene(self, locus):
		"""	returns GeneMap[locus] 
		"""
		try:
			return self.GeneMap[locus]
		except IndexError:
			error("Gene_def: incorrect locus")

	def get_locus(self, gene_name):
		"""	returns the gene's locus 
		"""
		for g in self.GeneMap:
			if g.name == gene_name:
				return g.locus
		error("Genetic_map: unknown gene name: " + str(gene_name))
		return None

	def get_gene_name(self, locus):
		"""	finds the name of the gene at locus 
		"""
		return self.get_gene(locus).name

	def get_gene_names(self):
		"""	returns genes' names as a list 
		"""
		return [g.name for g in self.GeneMap]
	
	def get_gene_boundaries(self,locus):
		"""	finds the gene's boundaries on the DNA 
		"""
		return (self.get_gene(locus).start, self.get_gene(locus).end)

	def get_coding(self, locus):
		"""	returns the gene's coding type (weighted, unweighted, ...) 
		"""
		return self.get_gene(locus).coding
		
	def gene_boundaries(self, gene_name):
		""" finds the gene's boundaries on the DNA 
		"""
		return get_boundaries(self, get_locus(self, gene_name))

	def geneMap_length(self):
		"""	location of the end of the last gene on Genemap 
		"""
		return self.get_gene(len(self.GeneMap)-1).end

	def locus_range(self, Locus):
		"""	returns the maximal amplitude of the gene at Locus 
		"""
		coding = self.get_gene(Locus).coding.lower()
		if coding in ['weighted', 'gray']:
			# Usual integer coding
			return (1 << self.get_gene(Locus).length ) - 1
		elif coding == 'unweighted':
			# Genes are coded as the number of 1s on the DNA section
			return self.get_gene(Locus).length
		elif coding == 'nocoding':
			return 1
		else:
			error("Genetic Map", 'unknown binary coding mode: %s' % str(coding))

	def gene_range(self, gene_name):
		"""	returns the maximal amplitude of the gene  
		"""
		return self.locus_range(self.get_locus(gene_name))

	def gene_pattern(self):
		"""	returns a binary mask showing gene alternation on DNA 
		"""
		G = 0
		pattern = []
		for g in self.GeneMap:
			pattern += [G] * g.length
			G = 1 - G
		return tuple(pattern)
		
	def __str__(self):
		return "Genetic map:\n\t" + '\n\t'.join([g.__str__() for g in self.GeneMap])
	 


if __name__ == "__main__":
	print(__doc__)
	print(Gene_def.__doc__)
	print(Genetic_map.__doc__ + '\n')




###################################
# Test                            #
###################################

if __name__ == "__main__":
	from Evolife.Scenarii.Parameters import Parameters
	class GMTest(Genetic_map, Parameters):
		def __init__(self):
			Parameters.__init__(self,'../Evolife.evo')
			Genetic_map.__init__(self,[('sex',1), ('prems',4),('deuze',7),('terce',2)])
	GeneMap = GMTest()
	print(GeneMap)
	print('pattern: '),
	print(GeneMap.gene_pattern())
	raw_input('[Return]')


__author__ = 'Dessalles'

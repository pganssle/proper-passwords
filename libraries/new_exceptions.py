'''
Library containing various exceptions

@author Paul J. Ganssle
@since 2014-04
'''

class OutOfSyncError(Exception):
	'''
	Error raised if a class with synchronized variables somehow becomes out of sync.
	'''
	pass


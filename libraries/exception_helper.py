'''
Library containing various generic exceptions.

@author Paul J. Ganssle
@since 2014-04
'''

class OutOfSyncError(Exception):
	'''
	Error raised if a class with synchronized variables somehow becomes out of sync.
	'''
	pass

class FileExists(IOError):
	'''
	Error raised if a file exists.
	'''
	pass

class RandomnessSourceUndefined(Exception):
	'''
	Raised when no source of randomness has been defined.
	'''
	pass
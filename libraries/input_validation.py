'''
Input validation library
Library for easy validation of common inputs.

@author Paul J. Ganssle
@since 2014-04
'''
import warnings

def valid_string_type(input, throw_error=False, warn=False, repr_on_fail=False,
						string_types=(str,unicode)):
	'''
	Check if the string is valid, with various contingencies defined.

	@param throw_error Throw an error if the string is not valid. [Default: False]
	@type throw_error bool

	@param warn Raise a warning if the string is not valid [Default: False]
	@type warn bool

	@param repr_on_fail Return the value printed to a string if it's not an instance of a 
						 string type. [Default: False] 
	@type repr_on_fail bool

	@param string_types Valid string types. Default: (str, unicode)
	@type type or tuple of types

	@return Returns boolean value of whether the string validated or not if repr_on_fail is false.
	        If repr_on_fail is true, returns repr(input) or input if the string is already valid.

	@throws NotStringTypeError Raised if parameter throw_error is true and string does not validate.
	@throws NotStringTypeWarning Raised if parameter warn is true and string does not validate.
	'''

	if not isinstance(input, string_types):
		if throw_error:
			raise NotStringTypeError('Type is '+type(input).__name__+' with value '+repr(input))

		if warn:
			warnings.warn('Invalid string type', NotStringTypeWarning)

		return repr(input) if repr_on_fail else False
	else:
		return input if repr_on_fail else True



# Exceptions
class NotStringTypeError(TypeError):
	'''
	Raised if the string is not a valid string type.
	'''
	pass

class NotStringTypeWarning(Warning):
	'''
	Raised if the string is not a valid string type.
	'''
	pass

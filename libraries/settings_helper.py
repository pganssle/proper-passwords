'''
Settings Helper Library
Provides a clean API for reading and writing settings.

@author Paul J. Ganssle
@since 2014-04
'''

import os, json
from shutil import copyfile
from input_validation import valid_string_type

class SettingsHelper:
	'''
	Static class with useful variables.
	'''
	# Where to find relevant things
	base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
	pref_dir = os.path.join(base_dir, 'preferences')
	source_dir = os.path.join(base_dir, 'sources')
	settings_loc = os.path.join(pref_dir, 'settings.json')
	default_settings_loc = os.path.join(base_dir, 'default_settings.json')
	settings_version = 0.1

	# Settings keys
	version_key = 'version'
	markov_source_loc_key = 'markov_source_loc'

class SettingsReader:
	'''
	Read-only access to the settings file.
	'''

	# Settings file location, defined relative to the location of this library.
	_read_file_loc = ''
	_settings_dict = None
	_settings_replacements = {'$base_dir' : SettingsHelper.base_dir,
							  '$pref_dir' : SettingsHelper.pref_dir,
							  '$source_dir' : SettingsHelper.source_dir}

	def __init__(self, file_loc=SettingsHelper.settings_loc):
		'''
		Constructor for the settings reader, reads the settings into a dict. The settings file
		should be a single dict, encoded with JSON.

		@throws NoSettingsFileError Thrown when settings file does not exist.
		@throwns BadSettingsFileError Thrown when settings file does not contain a JSON object
									  containing a settings dictionary.
		'''

		if not os.path.exists(file_loc):
			raise NoSettingsFileError('Settings file not found at '+file_loc)

		self._read_file_loc = file_loc

		with open(file_loc, 'r') as settings_file_object:
			self._settings_dict = json.load(settings_file_object)

		# Check the current version (check for validity)
		if SettingsHelper.version_key not in self._settings_dict.keys():
			raise BadSettingsFileError('Settings file version not found')
		
		self._file_version = self._settings_dict[SettingsHelper.version_key]

	def getValue(self, key):
		'''
		Retrieve the value of the setting.

		@param key The name of the setting.
		@type key str

		@return Returns the value of the setting.

		@throws InvalidSettingError Thrown if an invalid setting is requested.
		'''

		return self._parse_setting(self.getRawValue(key))

	def getRawValue(self, key):
		'''
		Retrieve the raw, un-parsed value of the setting.

		@param key The name of the setting
		@type key str

		@return Returns the raw value of the setting

		@throws KeyError Thrown if an invalid setting is requested.
		'''
		if not self.hasSetting(key):
			raise InvalidSettingError('Setting "'+key+'" not found in the settings file.')

		return self._settings_dict[key]

	def hasSetting(self, key):
		'''
		Check if a setting exists.

		@return Returns True if the setting is in the settings dictionary, false otherwise.
		'''
		return key in self._settings_dict.keys()

	def _parse_setting(self, setting_value):
		'''
		Some string settings include local variables. This method replaces them.
		The possible variables are:

		$base_dir		The path to the install directory.
		$pref_dir 		The path to the preferences directory
		$source_dir 	The path to the sources directory

		@param setting_value The value of the setting.
		@type setting_value any
		
		@return Returns the parsed value of the setting. If this is not a string, the raw value is
				returned.
		'''

		if not valid_string_type(setting_value, throw_error=False):
			return setting_value

		for key in self._settings_replacements.keys():
			setting_value = setting_value.replace(key, self._settings_replacements[key])

		return setting_value

class SettingsWriter(SettingsReader):
	'''
	Helper class for altering the settings file.
	'''
	_save_file_loc = ''

	def __init__(self, load_file=SettingsHelper.settings_loc, 
			           save_file_loc=SettingsHelper.settings_loc):
		'''
		Constructor for the settings writer.

		@param load_file The the settings file upon which to base the settings. If this is a dict, 
						 it is assumed to be an already-loaded settings dictionary. 
		@type load_file str or dict

		@param save_file_loc Where to save the changes to the file.
		@type save_file_loc str

		@throws NoSettingsFileError Thrown when the old settings file does not exist.
		@throws BadSettingsFileError Thrown when the old settings file is not valid.
		'''
		if isinstance(load_file, dict):
			self._settings_dict = load_file
		else:
			super(SettingsWriter, self).__init__(file_loc=load_file)

		self._save_file_loc=save_file_loc


	def setValue(self, key, setting_value):
		'''
		Alter a value in the settings dictionary.
		'''
		if not self.hasSetting(key):
			raise InvalidSettingError('Could not find setting "'+key+'" in settings dictionary.')

		# JSON cannot handle None values.
		if setting_value is None:
			raise InvalidSettingValue('Cannot store NoneType in settings file.')

		self._settings_dict[key] = setting_value

	def writeValues(self):
		'''
		Write the changes to file.
		'''

		# Make the directory if it does not exist
		if not os.path.exists(os.path.dirname(self._save_file_loc)):
			os.makedirs(os.path.dirname(self._save_file_loc))

		with open(self._save_file_loc, 'w+') as settings_file:
			json.dump(self._settings_dict, fp=settings_file, 
				      indent=4, 						# Pretty print
				      separators=(',', ': '))			# No trailing whitespace

def restore_default_settings():
	'''
	Restores the default settings.

	@throws IOError Thrown if the default settings file is not readable or the settings file is not
	                writable.
	'''
	if not os.path.exists(SettingsHelper.default_settings_loc):
		generate_default_settings_file()

	copyfile(SettingsHelper.default_settings_loc, SettingsHelper.settings_loc)


def generate_default_settings_file(file_loc=SettingsHelper.default_settings_loc):
	'''
	Generates a default settings file.

	@param file_loc Location to generate the default settings file in.
	@type file_loc str
	'''
	# Make the directory if it does not exist
	if not os.path.exists(os.path.dirname(file_loc)):
		os.makedirs(os.path.dirname(self._save_file_loc))

	# The default settings dictionary:
	settings_dict = dict()
	settings_dict[SettingsHelper.version_key] = SettingsHelper.settings_version
	settings_dict[SettingsHelper.markov_source_loc_key] = '$source_dir/markov_sources'

	# Save the file
	SW = SettingsWriter(load_file=settings_dict, save_file_loc=file_loc)
	SW.writeValues();



# Exceptions
class NoSettingsFileError(Exception):
	'''
	Raised when no settings file exists.
	'''
	pass

class BadSettingsFileError(Exception):
	'''
	Raised when a settings file exists, but does not contain a JSON object encoding a settings
	dictionary.
	'''
	pass

class InvalidSettingError(KeyError):
	'''
	Raised when an invalid setting is requested for reading or writing.
	'''
	pass

class InvalidSettingValue(ValueError):
	'''
	Raised when an invalid value is passed to a setting.
	'''
	pass
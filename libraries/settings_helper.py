'''
Settings Helper Library
Provides a clean API for reading and writing settings.

@author Paul J. Ganssle
@since 2014-04
'''

import os, json

class SettingsHelper:
	'''
	Static class with useful variables.
	'''
	base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
	pref_dir = os.path.join(base_dir, 'preferences')
	source_dir = os.path.join(base_dir, 'sources')
	settings_loc = os.path.join(base_dir, 'settings.json')
	settings_version = 0.1

	# Settings keys
	version_key = 'version'
	markov_source_loc_key = 'markov_source_loc'

class SettingsWriter:
	'''
	Helper class for altering the settings file.
	'''
	pass

class SettingsReader:
	'''
	Read-only access to the settings file.
	'''

	# Settings file location, defined relative to the location of this library.
	_settings_dict = None
	_settings_replacements = {'$base_dir' : SettingsHelper.base_dir,
							  '$pref_dir' : SettingsHelper.pref_dir,
							  '$source_dir' : SettingsHelper.source_dir}

	def __init__(self):
		'''
		Constructor for the settings reader, reads the settings into a dict. The settings file
		should be a single dict, encoded with JSON.

		@throws NoSettingsFileError Thrown when settings file does not exist.
		@throwns BadSettingsFileError Thrown when settings file does not contain a JSON object
									  containing a settings dictionary.
		'''

		if not os.path.exists(__settings_loc):
			raise NoSettingsFileError('Settings file not found at '+SettingsHelper.__settings_loc)

		with open(SettingsHelper.__settings_loc, 'r') as settings_file_object:
			self._settings_dict = json.load(settings_file_object)

		# Check the current version (check for validity)
		if SettingsHelper._version_key not in self._settings_dict.keys():
			raise BadSettingsFileError('Settings file version not found')
		
		self._file_version = self._settings_dict[SettingsHelper.version_key]

	def getValue(self, key):
		'''
		Retrieve the value of the setting.

		@param key The name of the setting.
		@type key str

		@return Returns the value of the setting.

		@throws KeyError Thrown if an invalid setting is requested.
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
		if not hasSetting(key):
			raise KeyError('Setting "'+key+'" not found in the settings file.')

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

		if not isinstance(setting_value, str):
			return setting_value

		for key in self._settings_replacements.keys():
			setting_value = setting_value.replace(key, self._settings_replacements[key])

		return setting_value

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
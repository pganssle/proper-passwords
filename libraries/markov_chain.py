'''
Library for arbitrary Markov chain generation

@author Paul J. Ganssle
@since 2014-04
'''
import re, json, os, random
import input_validation
from exception_helper import OutOfSyncError, FileExists, RandomnessSourceUndefined
from settings_helper import SettingsHelper, SettingsReader

_markov_ext = '.mjson'      # Markov JSON

class MarkovDB:
    '''
    This class is a database that can be used to generate Markov chains. 
    
    The source is stored in the MarkovDB object as an ordered list, and when generate() is called, 
    a list of all unique states is generated and used as the keys to a dictionary. The dictionary 
    entries are a list of all the positions at which each state appears in the source.

    To get the next entry in chain, an initial state is fed to the database, and a random entry is 
    selected from the dictionary entry for that state, and the next state is the next state in the 
    source.
    '''
    
    __db_version__ = 0.1                        # Include for future compatibility.

    # Private variables
    _source = None
    _state_index = []
    _state_positions = []
    _state_occurances = []
    _included_states = 0
    _valid_source = False
    _db_generated = False
    _rng = None
    name = ''

    # Methods
    def __init__(self, name, source=None, min_state_length=1, max_state_length=1):
        '''
        The constructor for the class.
        
        @param name The name of the database. This will be used for file saving, so special 
                    characters are not allowed.
        @type name str

        @param source An ordered list of states to be used in the Markov chain.
        @type source (str, list, tuple, dict)
        
        @param min_state_length The minimum number of consecutive entries in the source which can 
                                be considered a single state.
        @type min_state_length int
        
        @param max_state_length The maximum number of consecutive entries in the source that can
                                 be considered a single state.
        @type max_state_length int

        @throws TypeError Thrown if an invalid type is passed to one of the arguments.
        @throws ValueError Thrown if an invalid value is passed to one of the arguments.
        '''
        
        # Validate the inputs
        input_validation.valid_string_type(name, throw_error=True)

        if source is None:
            self._valid_source = False
        elif not isinstance(source, (str, list, tuple, dict)):
            raise TypeError('Source must be an ordered list or string.')
        else:
            self._valid_source = True

        if re.match('^[\w_ -]+$', name) is None:
            raise ValueError('"name" can only contain alphanumeric characters, spaces, dashes '+\
                             ' and underscores.')

        if min_state_length < 1:
            raise ValueError('min_state_length must be a positive integer.')

        if max_state_length < 1:
            raise ValueError('max_state_length must be a positive integer.')

        # Construct the object
        self.name = name
        self._source = source
        self.min_state_length=min_state_length
        self.max_state_length=max_state_length
        self._rng = random.SystemRandom()
    
    def generate(self):
        '''
        Generates the Markov database from the source by finding each unique state in the source and
        adding it to the _state_* attributes.

        @throws InvalidMarkovSourceError Thrown when no valid source is present.
        '''
        if not self._valid_source:
            raise InvalidMarkovSourceError('Valid source must be provided before '+\
                                           'generating database.')
        
        # Start by finding each unique state in the source and adding it to the "state" attributes.
        for ii in range(0, len(self._source)):
            # Each state can include a number of entries in the source
            for jj in range(self.min_state_length, self.max_state_length+1):
                # Stop if we hit the end of the source entry. 
                if ii + jj >= len(self._source):
                    break

                # Generate a state from the source then call the _add_state method
                state = self._source[ii:ii+jj]
                self._add_state(state, ii)

        self._db_generated = True

    def save(self, save_location=None, overwrite=True):
        '''
        Save the database to a json file so that it does not need to be generated from the source 
        with each new instance.

        @param save_location The directory into which the file should be saved. [Default: None]
        @type save_location str

        @throws TypeError Raised when argument inputs are of the wrong type.
        @throws InvalidMarkovSourceError Raised when no valid markov source is present.
        @throws MarkovDBNotGeneratedError Raised when the Markov database has not been generated.
        '''
        if not self._valid_source:
            raise InvalidMarkovSourceError('Markov source must be valid and the database must '+\
                                           'generated before saving to file.')

        if not self._db_generated:
            raise MarkovDBNotGeneratedError('Markov database must be generated before '+\
                                            'saving to file.')

        if save_location is None:
            # Use the default location, check the settings file.
            save_location = SettingsReader().getValue(SettingsHelper.markov_source_loc_key)

        save_file_path = os.path.join(save_location, self.name+_markov_ext)
        if not overwrite and os.path.exists(save_file_path):
            raise FileExists('Markov database file '+self.name+_markov_ext+' already exists.')

        # Turn this into a dictionary for JSON serialization
        markov_dict = dict()
        markov_dict['version'] = self.__db_version__
        markov_dict['name'] = self.name
        markov_dict['source'] = self._source
        markov_dict['state_index'] = self._state_index
        markov_dict['state_positions'] = self._state_positions
        markov_dict['state_occurances'] = self._state_occurances
        markov_dict['included_states'] = self._included_states

        # Save the file with JSON
        if not os.path.exists(os.path.dirname(save_file_path)):
            os.makedirs(os.path.dirname(save_file_path))

        with open(save_file_path, 'w+') as save_file:
            json.dump(markov_dict, fp=save_file,
                indent=4,
                separators=(',', ': '))

        
    def load(self, file_path=None):
        '''
        Load a saved database from file.

        @param file_path The path of the file to load. If None, this will be generated from the 
                         default save location and the name passed to the constructor.
        @type file_path str

        @throws TypeError Raised when argument inputs are of the wrong type.
        @throws ValueError Raised when an invalid path is passed to file_path
        '''
        if file_path is None:
            file_path = os.path.join(SettingsReader().getValue(\
                                     SettingsHelper.markov_source_loc_key), self.name+_markov_ext)

        # Raise an error if this is an invalid string type.
        input_validation.valid_string_type(file_path, throw_error=True) 

        if not os.path.exists(file_path):
            raise ValueError('Path is not valid.')

        # Load the JSON file.
        with open(file_path, 'r') as mdb_file:
            markov_dict = json.load(mdb_file)
        try:
            self.name = markov_dict['name']
            self._source = markov_dict['source']
            self._state_index = markov_dict['state_index']
            self._state_occurances = markov_dict['state_occurances']
            self._included_states = markov_dict['included_states']
        except KeyError as ke:
            raise InvalidMarkovDatabaseFile('Error reading Markov file.', ke=ke)

        # Assuming this wasn't a malformed file, these are true as well.
        self._db_generated = True
        self._valid_source = True

    def get_chain(self, num_states):
        '''
        Generate a Markov chain with length num_states
        '''
        pass

    # Private methods
    def _get_next_state(self, state):
        '''
        Given a state, randomly choose a next state, drawn randomly from the possible choices.

        @param state A valid state.

        @return Returns another state.

        @throws InvalidMarkovStateError Thrown when an invalid state is passed.
        '''
        if state not in self._state_index:
            raise InvalidMarkovStateError('State '+repr(state)+' is not in the database.')

        if self._rng is None:
            raise RandomnessSourceUndefined('Cannot generate Markov chain without '+\
                                            'randomness source.')

        state_pos = self._state_index.index(state)
        source_pos = self._rng.choice(self._state_positions[state_pos])
        source_pos += len(self._state_index[state_pos]) # Move to the next state
        
        # States have a random length, so select one of the possible lengths.
        # randrange(x, y) generates random numbers in the range [x,y), so add 1 to max length
        state_length = self._rng.randrange(self.min_state_length, self.max_state_length+1)

        return self._source[source_pos:source_pos+state_length]

    def _add_state(self, state, position):
        '''
        Adds a state to the source index, etc.

        @param state A state, either a list or a single item.
        @param position The position of the state in the source.

        @throws OutOfSyncError Raised if somehow the _state_* attributes are out of sync.
        '''

        try:
            state_pos = self._state_index.index(state)
        except ValueError:
            # ValueError is thrown if the state is not in the state index, so add it.
            
            # First check that all three state functions are in sync.
            if not (len(self._state_index) == len(self._state_positions) == \
                    len(self._state_occurances)):
                raise OutOfSyncError('State attributes don\'t have identical lengths.')
                
            # Add the state to the _state attributes
            self._state_index.append(state)
            state_pos = len(self._state_index)-1

            # These two are empty because they are updated later
            self._state_positions.append([])
            self._state_occurances.append(0)

        # If this exact position has already been added to the database, don't do anything.
        if position not in self._state_positions[state_pos]:
            self._state_positions[state_pos].append(position)
            self._state_occurances[state_pos] += 1
            self._included_states += 1


# Exceptions
class InvalidMarkovStateError(KeyError):
    '''
    Raised if an invalid Markov state is requested.
    '''
    pass

class InvalidMarkovSourceError(Exception):
    '''
    Raised if trying to use an invalid Markov source.
    '''
    pass

class MarkovDBNotGeneratedError(Exception):
    '''
    Raised if the Markov database has not been generated, but needs to be.
    '''
    pass

class InvalidMarkovDatabaseFile(KeyError):
    '''
    Raised if the Markov database file is invalid.
    '''
    __KeyError = None
    def __init__(self, message='', ke=None, **kwargs):
        '''
        Can pass the specific KeyError that generated this as an argument.

        @param ke The KeyError generated from the missing variable.
        @type ke KeyError
        '''
        self.__KeyError = ke
        super(InvalidMarkovDatabaseFile, self).__init__(message)
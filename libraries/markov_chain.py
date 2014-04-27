'''
Library for arbitrary Markov chain generation

@author Paul J. Ganssle
@since 2014-04
'''
import re
from new_exceptions import OutOfSyncError

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
    _databaseCompiled = False
    _name = ''

    # Methods
    def __init__(self, name, source, min_state_length=1, max_state_length=1):
        '''
        The constructor for the class.
        
        @param name The name of the database. This will be used for file saving, so special characters are not allowed.
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
        if not isinstance(name, str):
            raise TypeError('Name must be a string')

        if not isinstance(source, (str, list, tuple, dict)):
            raise TypeError('Source must be an ordered list or string.')

        if re.match('^[\w_ -]+$', name) is None:
            raise ValueError('"name" can only contain alphanumeric characters, spaces, dashes and underscores.')

        if min_state_length < 1:
            raise ValueError('min_state_length must be a positive integer.')

        if max_state_length < 1:
            raise ValueError('max_state_length must be a positive integer.')

        # Construct the object
        self._name = name
        self._source = source
        self.min_state_length=min_state_length
        self.max_state_length=max_state_length
    
    def generate(self):
        '''
        Generates the Markov database from the source by finding each unique state in the source and adding it to the
        _state_* attributes.
        '''
        
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

    def save(self, save_location=None):
        '''
        Save the database to a file so that it does not need to be regenerated each time. It is not yet clear what
        format will be used for this.

        @param save_location The directory into which the file should be saved. [Default: None]
        @type save_location str

        @throws NotImplementedError This is not currently implemented.
        @throws TypeError Raised when argument inputs are of the wrong type.
        '''
        raise NotImplementedError('Saving databases has not yet been implemented.')

    def load(self, file_path=None):
        '''
        Load a saved database from file.

        @param file_path The path of the file to load. If None, this will be generated from the default save location 
                         and the name passed to the constructor.
        @type file_path str

        @throws NotImplementedError This is not currently implemented.
        @throws TypeError Raised when argument inputs are of the wrong type.
        @throws ValueError Raised when an invalid path is passed to file_path
        '''
        raise NotImplementedError('Loading databases has not yet been implemented.')

    def _add_state(self, state, position):
        '''
        Adds a state to the source index, etc.

        @param state A state, either a list or a single item.
        @param position The position of the state in the source.

        @raise OutOfSyncError Raised if somehow the _state_* attributes are out of sync.
        '''

        try:
            state_pos = self._state_index.index(state)
        except ValueError:
            # ValueError is thrown if the state is not in the state index, so add it.
            
            # First check that all three state functions are in sync.
            if not (len(self._state_index) == len(self._state_positions) == len(self._state_occurances)):
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
      
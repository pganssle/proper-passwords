'''
Library for arbitrary Markov chain generation

@author Paul J. Ganssle
@since 2014-04

@todo Separate out the Settings stuff into a separate file so that this can be used independently in
      unrelated projects.
'''
import re, json, os, random, zlib
from time import time
from sys import stdout
import input_validation
from copy import copy as cp
from exception_helper import OutOfSyncError, FileExists, RandomnessSourceUndefined
from settings_helper import SettingsHelper, SettingsReader

_markov_ext = '.mjson'      # Markov JSON
_m_zip = '.mjson.gz'        # Compressed JSON.

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

    # Methods
    def __init__(self, name, source=None, min_state_length=1, max_state_length=1,
                       delimiter=None):
        '''
        The constructor for the class.
        
        @param name The name of the database. This will be used for file saving, so special 
                    characters are not allowed.
        @type name str

        @param source An ordered list of states to be used in the Markov chain.
        @type source (str, unicode, list, tuple, dict)
        
        @param min_state_length The minimum number of consecutive entries in the source which can 
                                be considered a single state.
        @type min_state_length int
        
        @param max_state_length The maximum number of consecutive entries in the source that can
                                 be considered a single state.
        @type max_state_length int

        @param delimiter Delimiter marks the end of a given state (space for words, . for sentences,
                          etc.) If None then no delimiter is used. The delimiter will be included in
                          the states.
        @type delimiter state 

        @throws TypeError Thrown if an invalid type is passed to one of the arguments.
        @throws ValueError Thrown if an invalid value is passed to one of the arguments.
        '''
        
        # Validate the inputs
        input_validation.valid_string_type(name, throw_error=True)

        if re.match('^[\w_ -]+$', name) is None:
            raise ValueError('"name" can only contain alphanumeric characters, spaces, dashes '+\
                             ' and underscores.')

        if min_state_length < 1:
            raise ValueError('min_state_length must be a positive integer.')

        if max_state_length < 1:
            raise ValueError('max_state_length must be a positive integer.')
        
        # Basic values
        self._source = None
        self._source_by_state = []           # States beginning at each position in the source.
        self._state_index = []
        self._state_delimited = []
        self._state_positions = []
        self._state_occurances = []
        self._included_states = 0
        self._valid_source = False
        self._db_generated = False
        self._rng = random.SystemRandom()
        self._saved_loc = None
        
        # Construct the object
        self.name = name
        if source is not None:
            self._add_source(source)

        self._delimiter = delimiter

        self.min_state_length=min_state_length
        self.max_state_length=max_state_length
        self._rng = random.SystemRandom()
    
    def generate(self, print_progress=False, print_time=False):
        '''
        Generates the Markov database from the source by finding each unique state in the source and
        adding it to the _state_* attributes.

        @param print_progress Print a progress bar as you are going [Default: False]
        @type print_progress bool

        @param print_time Print the time that the generation took.
        @type print_time bool

        @throws InvalidMarkovSourceError Thrown when no valid source is present.
        '''
        if not self._valid_source:
            raise InvalidMarkovSourceError('Valid source must be provided before '+\
                                           'generating database.')
        
        # Set up the progress bar - basically approximate.
        if print_time:
            current_time_millis = lambda: int(round(time() * 1000))    # SO/questions/5998245/
            stime = current_time_millis()

        if print_progress:
            prog_len = 1.0*len(self._source)*(self.max_state_length-self.min_state_length+1)
            kk = 0; l_prog = -1; char_set = ('[', ']'); csi = 0

        # Start by finding each unique state in the source and adding it to the "state" attributes.
        for ii in range(0, len(self._source)):
            # Each state can include a number of entries in the source
            for jj in range(self.min_state_length, self.max_state_length+1):
                # Stop if we hit the end of the source entry. 
                if ii + jj > len(self._source):
                    break

                # Generate a state from the source then call the _add_state method
                state = self._source[ii:ii+jj]
                delimiter_found = self._add_state(state, ii)
                
                if print_progress:
                    kk += 1
                    c_prog = kk/prog_len
                    if c_prog-l_prog >= 0.05:
                        # Update every 5% 
                        l_prog = round(c_prog*20)/20.0
                        stdout.write(char_set[csi%2]);    csi += 1
                        stdout.flush()

                # Break if we've hit a delimiter.
                if delimiter_found:
                    break

        # Print a newline at the end if we're printing the progress.
        if print_progress:
            if csi%2 == 1:
                stdout.write(']')
            stdout.write('\n')

        if print_time:
            time_elapsed = (current_time_millis() - stime)/1000.0;
            hours = int(time_elapsed/3600); time_elapsed -= hours*3600
            minutes = int(time_elapsed/60); time_elapsed -= minutes*60
            seconds = time_elapsed
            if hours > 0:
                stdout.write('{:0.0f}h '.format(hours))
            if minutes > 0:
                stdout.write('{:0.0f}m '.format(minutes))

            stdout.write('{:02.3f}s\n'.format(seconds))

        self._db_generated = True

    def save(self, save_location=None, overwrite=True, compress=True):
        '''
        Save the database to a json file so that it does not need to be generated from the source 
        with each new instance.

        @param save_location The directory into which the file should be saved. [Default: None]
        @type save_location str

        @throws TypeError Raised when argument inputs are of the wrong type.
        @throws InvalidMarkovSourceError Raised when no valid markov source is present.
        '''
        if not self._valid_source:
            raise InvalidMarkovSourceError('Markov source must be valid before saving to file.')

        if save_location is None:
            if self._saved_loc is not None and os.path.exists(self._saved_loc):
                # Use the previous saving location if this has been saved before and 
                # the file is still there.
                save_location = os.path.dirname(self._saved_loc)
            else:
                # Else use the default location, check the settings file.
                save_location = SettingsReader().getValue(SettingsHelper.markov_source_loc_key)

        fext = _m_zip if compress else _markov_ext
        save_file_path = os.path.join(save_location, self.name+fext)
        if not overwrite and os.path.exists(save_file_path):
            raise FileExists('Markov database file '+self.name+fext+' already exists.')

        # Turn this into a dictionary for JSON serialization
        markov_dict = dict()
        markov_dict['version'] = self.__db_version__
        markov_dict['name'] = self.name
        markov_dict['source'] = self._source
        markov_dict['valid_source'] = self._valid_source
        markov_dict['db_generated'] = self._db_generated
        markov_dict['source_by_state'] = self._source_by_state
        markov_dict['state_index'] = self._state_index
        markov_dict['state_positions'] = self._state_positions
        markov_dict['state_occurances'] = self._state_occurances
        markov_dict['state_delimited'] = self._state_delimited
        markov_dict['included_states'] = self._included_states

        # Save the file with JSON
        if not os.path.exists(os.path.dirname(save_file_path)):
            os.makedirs(os.path.dirname(save_file_path))

        with open(save_file_path, 'w+') as save_file:
            if compress:
                cdata = zlib.compress(json.dumps(markov_dict))
                save_file.write(cdata)
            else:
                json.dump(markov_dict, fp=save_file,
                    indent=4,
                    separators=(',', ': '))


        self._saved_loc = save_file_path

        
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
            if os.path.exists(self._saved_loc):
                # For recalling a previous state.
                file_path = self._saved_loc
            else:
                base_fname = os.path.join(SettingsReader().getValue(\
                    SettingsHelper.markov_source_loc_key), self.name)
                
                decompressed_file_exists = os.path.exists(base_fname+_markov_ext)
                compressed_file_exists = os.path.exists(base_fname+_m_zip)

                if decompressed_file_exists and compressed_file_exists:
                    # Find out which one's newer.
                    if os.path.getmtime(base_fname+_markov_ext) >= \
                       os.path.getmtime(base_fname+_m_zip):
                        fext = _markov_ext
                    else:
                        fext = _m_zip
                elif decompressed_file_exists:
                    fext = _markov_ext
                else:
                    fext = _m_zip
                
                file_path = os.path.join(SettingsReader().getValue(\
                                     SettingsHelper.markov_source_loc_key), self.name+fext)

        # Raise an error if this is an invalid string type.
        input_validation.valid_string_type(file_path, throw_error=True) 

        if not os.path.exists(file_path):
            raise ValueError('Path is not valid.')

        # Load the JSON file.
        with open(file_path, 'r') as mdb_file:
            if file_path.endswith(_m_zip):  # Compressed
                ddata = zlib.decompress(mdb_file.read())
                markov_dict = json.loads(ddata)
            else:
                markov_dict = json.load(mdb_file)
        try:
            self.name = markov_dict['name']
            self._valid_source = markov_dict['valid_source']
            if self._valid_source:
                self._add_source(markov_dict['source'])
    
            self._db_generated = markov_dict['db_generated']

            if self._db_generated:
                self._source_by_state = markov_dict['source_by_state']
                self._state_index = markov_dict['state_index']
                self._state_occurances = markov_dict['state_occurances']
                self._included_states = markov_dict['included_states']
                self._state_delimited = markov_dict['state_delimited']

        except KeyError as ke:
            raise InvalidMarkovDatabaseFile('Error reading Markov file key '+ke.args[0], ke=ke)

        self._saved_loc = file_path

    def get_chain(self, num_states, 
                        seed=None, random_seed_weighted=False,
                        delimiter=None):
        '''
        Generate a Markov chain with length num_states
        @todo Replace integer validation with centralized method.

        @param num_states Number of states to be included in the chain.
        @type int

        @param seed The state with which to seed the state. If None is passed to this parameter, a 
                    state will be selected randomly.
        @type seed state

        @param random_seed_weighted If set to True, a random position in the source is chosen and a 
                                    a state is chosen from among those at this position. This only 
                                    applies if seed is None. [Default: False]
        @type random_seed_weighted bool

        @param delimiter Break if the chain encounters anything in this list. (Not implemented)
        @type delimiter (str, list, set, tuple)

        @return Returns a chain of states.
        
        @throws ValueError Thrown if num_states is not a positive integer.
        @throws InvalidMarkovStateError Thrown if seed is not a valid state.
        @throws MarkovDBNotGeneratedError Thrown if the Markov database has not been generated.
        @throws InvalidMarkovSourceError Thrown if the source is not valid.
        '''
        # Validate inputs.
        if num_states < 1:
            raise ValueError('Number of states must be a positive integer.')

        if not self._valid_source:
            raise InvalidMarkovStateError('Source must be valid and database generated before ' + \
                                          'a chain can be generated.')

        if not self._db_generated:
            raise MarkovDBNotGeneratedError('Markov database must be generated before a chain ' + \
                                            'can be generated.')

        # If we haven't been provided a state, choose one at random.
        if seed is None:
            if self._rng is None:
                raise RandomnessSourceUndefined('Randomness source needed for Markov chain '+\
                                                'generation.')

            if random_seed_weighted:
                seed_index = self._rng.choice(self._rng.choice(self._source_by_state))
                seed = self._state_index[seed_index]
            else:
                seed = self._rng.choice(self._state_index)

        # Validate the seed.
        if seed not in self._state_index:
            raise InvalidMarkovStateError(repr(seed) + ' is not a valid state.')

        # Generate the state
        chain = [seed]
        c_state = seed
        for ii in range(1, num_states):
            c_state, index = self._get_next_state(c_state)

            # Chain is broken if we reach the end of the source or if we reach a delimiter.
            if c_state is None or self._state_delimited[index]:
                break           

            chain.append(c_state)

        return chain

    def get_chain_as_string(self, num_states, 
                            seed=None, random_seed_weighted=False, 
                            delimiter=None):
        '''
        Call the get_chain method, then concatenate it to a string. This will only work if the 
        source material is also made of strings.

        @param num_states Number of states to be included in the chain.
        @type int

        @param seed The state with which to seed the state. If None is passed to this parameter, a 
                    state will be selected randomly.
        @type seed state

        @param random_seed_weighted If set to True, a random position in the source is chosen and a 
                                    a state is chosen from among those at this position. This only 
                                    applies if seed is None. [Default: False]
        @type random_seed_weighted bool

        @param delimiter Break if the chain encounters anything in this list. (Not implemented)
        @type delimiter (str, list, set, tuple)
        
        @return Returns a chain of states as a string.

        @throws TypeError Thrown if the source is not made up of strings or characters.
        @throws ValueError Thrown if num_states is not a positive integer.
        @throws InvalidMarkovStateError Thrown if seed is not a valid state.
        '''
        chain = self.get_chain(num_states=num_states, 
                               seed=seed, 
                               random_seed_weighted=random_seed_weighted)

        out_chain = ''
        for state in chain:
            input_validation.valid_string_type(state, throw_error=True)

            out_chain += state

        return out_chain

    # Private methods
    def _add_source(self, source):
        '''
        Adds a source if no valid source is present.

        @param source A valid ordered list of some type.
        @type source (str, unicode, list, dict, tuple)
        '''
        # Input Validation
        if not isinstance(source, (str, unicode, list, tuple, dict)):
            raise TypeError('Source must be an ordered list or string, given '+\
                            type(source).__name__)
        
        self._source = cp(source)
        self._source_by_state = [[] for x in range(0, len(source))]
        self._valid_source = True

    def _get_next_state(self, state):
        '''
        Given a state, randomly choose a next state, drawn randomly from the possible choices.

        @param state A valid state.

        @return (state, state_index)

        @throws InvalidMarkovStateError Thrown when an invalid state is passed.
        '''
        if state not in self._state_index:
            raise InvalidMarkovStateError('State '+repr(state)+' is not in the database.')

        if self._rng is None:
            raise RandomnessSourceUndefined('Cannot generate Markov chain without '+\
                                            'randomness source.')

        state_pos = self._state_index.index(state)
        source_pos = self._rng.choice(self._state_positions[state_pos])
        source_pos += len(self._state_index[state_pos])     # Move to the next state in the source.
        
        # Choose randomly from among the states starting at the next position (there will likely be
        # one for each state length.
        if source_pos > len(self._source_by_state) or len(self._source_by_state[source_pos]) < 1:
            return None
        else:                       # Unnecessary but preferred for aesthetic reasons.
            state_index = self._rng.choice(self._source_by_state[source_pos])
            return (self._state_index[state_index], state_index)

    def _add_state(self, state, position):
        '''
        Adds a state to the source index, etc.

        @param state A state, either a list or a single item.
        @param position The position of the state in the source.

        @throws OutOfSyncError Raised if somehow the _state_* attributes are out of sync.
        @throws KeyError Raised if position is invalid in the source.

        @return Returns whether or not the state ends with the delimiter.
        '''
        if not 0 <= position < len(self._source):
            raise KeyError(repr(position)+' is not a valid index to the source.')

        try:
            state_pos = self._state_index.index(state)
        except ValueError:
            # ValueError is thrown if the state is not in the state index, so add it.
            
            # First check that all three state functions are in sync.
            if not (len(self._state_index) == len(self._state_positions) == \
                    len(self._state_occurances) == len(self._state_delimited)):
                raise OutOfSyncError('State attributes don\'t have identical lengths.')
                
            # Add the state to the _state attributes
            self._state_index.append(state)
            state_pos = len(self._state_index)-1

            # These two are empty because they are updated later
            self._state_positions.append([])
            self._state_occurances.append(0)

            # We'll assume that we don't have delimiters in the middle of the state, based on
            # how .generate() works.
            if self._delimiter is not None:
                self._state_delimited.append(self._delimiter in state)
            else:
                self._state_delimited.append(False) # Never true with no delimiter

        # If this exact position has already been added to the database, don't do anything.
        if position not in self._state_positions[state_pos]:
            self._state_positions[state_pos].append(position)
            self._state_occurances[state_pos] += 1
            self._included_states += 1

        if state_pos not in self._source_by_state[position]:
            self._source_by_state[position].append(state_pos)

        return self._state_delimited[state_pos]


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
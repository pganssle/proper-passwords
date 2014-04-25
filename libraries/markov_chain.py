'''
Library for arbitrary Markov chain generation

@author Paul J. Ganssle
@since 2014-04
'''
import re

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
    _sourceDB = None
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

        if re.match('^[\w_- ]+$', string) is None:
            raise ValueError('"name" can only contain alphanumeric characters, spaces, dashes and underscores.')

        if min_state_length < 1:
            raise ValueError('min_state_length must be a positive integer.')

        if max_state_length < 1:
            raise ValueError('max_state_length must be a positive integer.')

        # Construct the object
        self.__name = name
        self.__source = source
        self.min_state_length=min_state_length
        self.max_state_length=max_state_length
    
    def generate(self):
        '''
        Generates the Markov database from the source.

        @throws NotImplementedError This is not currently implemented. This will change soon.
        '''
        raise NotImplementedError('Database generation has not yet been implemented.') 

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

      
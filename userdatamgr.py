import json
import os
import logging
from configs import LOCAL_FOLDER_NAME, DB_FILE_NAME
from file_utils import write_to_json, load_json

DEFAULT_FILENAME = os.path.join(LOCAL_FOLDER_NAME, DB_FILE_NAME)

class UDManager:
    INITIAL_TABLE = {
        "users":{},
        "modules":{}
    }
    
    def __init__(self, filepath = DEFAULT_FILENAME):
        self.filepath = filepath
        self._init_data(self.INITIAL_TABLE)

    def _init_data(self, data):
        self.data = data
        if (not "users" in data) or (not "modules" in data):
            logging.warn("Loaded userdata file does not have correct structure. Loading from blank. This might irreversibly overwrite the existing JSON!")
            self.data = self.INITIAL_TABLE
        self.users = self.data["users"]
        self.modules = self.data["modules"]
    
    # REPLACES current STATE DATA
    def load(self):
        if not self.data == self.INITIAL_TABLE:
            print("<DBManager load> Attempting to load from file when DATA NOT EMPTY")

        self._init_data(load_json(self.filepath))
        logging.info("Loaded successfully!")

    def write_to_file(self):
        write_to_json(self.filepath, self.data)

    # Internal method
    # If user doesnt exist, return a blank dict
    def get_user(self, userID):
        out = self.users.get(userID, {})
        if not out:
            logging.warn("User %s does not exist" % userID,)
        return out

    # Called only by write
    def _create_user(self, userID):
        assert not userID in self.users 
        self.users[userID] = {}
        logging.warn("Created User: '%s'" % userID)
        return self.users[userID]

    # Writes the given value to the key the user's table 
    # OVERWRITES any existing data
    def write_to_user(self, userID, user_data):
        if not self.get_user(userID):
            self._create_user(userID)
        self.users[userID] = user_data
        self.write_to_file() # WRITE TO FILE AFTER EVERY UPDATE

    def _write_value_to_module(self, module_code, key, value):
        if not module_code in self.modules:
            self._create_module(module_code)
        self.modules[module_code][key] = value
        self.write_to_file()

    # Boolean UNUSED
    def user_exists(self, userID):
        return (not self.get_user(userID) == False)

    def _create_module(self, modcode):
        assert not modcode in self.modules 
        self.modules[modcode] = {}
        logging.warn("Created Module: '%s'" % modcode)
        return self.modules[modcode]
 
    def write_user_to_module(self, module_code, userID, info):
        self._write_value_to_module(module_code, userID, info)

    def get_module(self, module_code):
        return self.modules.get(module_code, {})


# TESTS
# test = UDManager()
# test.load()
# test.write_to_file()
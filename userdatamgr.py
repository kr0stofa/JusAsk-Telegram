import json
import os
import logging
from configs import LOCAL_FOLDER_NAME, DB_FILE_NAME
from file_utils import write_to_json, load_json

DEFAULT_FILENAME = os.path.join(LOCAL_FOLDER_NAME, DB_FILE_NAME)

class UDManager:
    def __init__(self, filepath = DEFAULT_FILENAME):
        self.filepath = filepath
        self.data = {}

    # REPLACES THE DATA
    def load(self):
        if not self.data == {}:
            print("<DBManager load> Attempting to load from file when DATA NOT EMPTY")

        self.data = load_json(self.filepath)
        logging.info("Loaded successfully!")

    def write_to_file(self):
        write_to_json(self.filepath, self.data)

    # Returns false if the user doesnt have this 

    # Internal method
    # If user doesnt exist, return a blank dict
    def get_user(self, userID):
        out = self.data.get(userID, {})
        if not out:
            logging.warn("User %s does not exist" % userID,)
        return out

    # Called only by write
    def _create_user(self, userID):
        assert not userID in self.data 
        self.data[userID] = {}
        logging.warn("Created User: '%s'" % userID)
        return self.data[userID]

    # Writes the given value to the key the user's table 
    # OVERWRITES any existing data
    def write_to_user(self, userID, user_data):
        if not self.get_user(userID):
            self._create_user(userID)
        self.data[userID] = user_data
        self.write_to_file() # WRITE TO FILE AFTER EVERY UPDATE

    # Boolean UNUSED
    def user_exists(self, userID):
        return (not self.get_user(userID) == False)


# TESTS
# test = UDManager()
# test.load()
# test.write_to_file()
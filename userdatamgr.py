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

        try:
            with open(self.filepath, 'r') as readfile:
                self.data = json.load(readfile)
        
        except Exception as e:
            print("<DBManager load> Exception! ", e)
            logging.error("DBManager failed to load")

        logging.info("Loaded successfully!")

    def write_to_file(self):
        write_to_json(self.filepath, self.data)

    def get_user_value(self, uid, key):
        return self._get_user(uid).get(key)

    # Internal method
    def _get_user(self, userID):
        return self.data.get(userID, False)

    # Called only by write
    def _create_user(self, userID):
        assert not userID in self.data 
        self.data[userID] = {}
        return self.data[userID]

    # Writes to the 
    def _write_to_user(self, userID, key, value):
        user = self._get_user(userID)
        if not user:
            user = self._create_user(userID)
        user[key] = value

    # Boolean
    def user_exists(self, userID):
        return (not self._get_user(userID) == False)

    # PM methods
    def add_to_pmtable(self, userID, chatID):
        self._write_to_user(userID, "chatID", chatID)
        return
    
    def get_chatID(self, userID):
        return self.get_user_value(userID, "chatID")

    # MODULE methods
    def add_senior_modules(self, userID, senior_mods):
        self._write_to_user(userID, "senior_modules", senior_mods)
        return

test = UDManager()
test.load()
test.write_to_file()
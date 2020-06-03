import json
import os
import logging
from configs import LOCAL_FOLDER_NAME, SD_FILE_NAME
from file_utils import load_json

DEFAULT_FILENAME = os.path.join(LOCAL_FOLDER_NAME, SD_FILE_NAME)

class SDManager:
    def __init__(self, filepath = DEFAULT_FILENAME):
        self.filepath = filepath
        self.data = {}

    def load(self):
        if not self.data == {}:
            print("<SDManager load> Attempting to load from file when DATA NOT EMPTY")
        self.data = load_json(self.filepath)

    def _get_mods(self, sch):
        MOD_KEY = "modules"
        sch_dict = self.data.get(sch, False)
        if not sch_dict:
            logging.error("No such school %s" % sch)
        else:
            assert MOD_KEY in sch_dict
            # change to list of keys
            return list(sch_dict[MOD_KEY].keys())

    def get_modlist(self, school):
        return self._get_mods(school)
        
    def mod_exists(self, school, mod):
        mods = self._get_mods(school)
        return (mod in mods)

test = SDManager()
test.load()
print(test.get_modlist("NUS"))
import json
import os
import logging
from configs import LOCAL_FOLDER_NAME, SD_FILE_NAME

DEFAULT_FILENAME = os.path.join(LOCAL_FOLDER_NAME, SD_FILE_NAME)

class SDManager:
    def __init__(self, filepath = DEFAULT_FILENAME):
        self.filepath = filepath
        self.data = {}

    # REPLACES THE DATA
    def load(self):
        if not self.data == {}:
            print("<SDManager load> Attempting to load from file when DATA NOT EMPTY")

        try:
            with open(self.filepath, 'r') as readfile:
                self.data = json.load(readfile)
        except Exception as e:
            print("<SDManager load> Exception! ", e)
            logging.error("SDManager failed to load")

    def _get_mods(self, sch):
        MOD_KEY = "modules"
        sch_dict = self.data.get(sch, False)
        if not sch_dict:
            logging.error("No such school %s" % sch)
        else:
            assert MOD_KEY in sch_dict
            return sch_dict.get[MOD_KEY]

    def get_modlist(self, school):
        return self._get_mods(school)
        
    def mod_exists(self, school, mod):
        mods = self._get_mods(school)
        return (mod in mods)

test = SDManager()
test.load()
print(test.data)
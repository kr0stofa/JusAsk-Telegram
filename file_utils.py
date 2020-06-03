import json
import logging

# Accepts a filepath string and data
# Converts to json when writing
def write_to_json(filepath, data):
    try:
        with open(filepath, 'w') as outfile:
            json.dump(data, outfile)
        logging.info("Wrote to %s successfully!" % filepath)
    except Exception as e:
        print("<WRITE_TO_JSON> Exception when trying to write %s! %s" % (filepath, e))
        logging.error("Failed to write to %s" % filepath)
        return {}
    

def load_json(filepath):
    data = {}
    try:
        with open(filepath, 'r') as readfile:
            data = json.load(readfile)
        logging.info("Loaded %s successfully!" % filepath)
        return data
    except Exception as e:
        print("<LOAD_JSON> Exception when trying to load %s! %s" % (filepath, e))
        logging.error("Failed to load from %s" % filepath)
        return {}
    
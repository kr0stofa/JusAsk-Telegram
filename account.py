import logging
from userdatamgr import UDManager

# Enums
k_chatid = "chatID"
k_fac = "faculty"
k_snrmods = "senior_modules"
k_yr = "year"

class Accounter:
    def __init__(self):
        self.udm = UDManager()
        self.udm.load()
        self.dnd_table = {}

    def _get_user_value(self, userID, key):
        user_data = self.udm.get_user(userID)
        return user_data.get(key, False)

    def _write_to_user_value(self, userID, key, value):
        user_data = self.udm.get_user(userID)
        user_data[key] = value
        self.udm.write_to_user(userID, user_data)
    
    # PM methods
    def add_to_pmtable(self, userID, chatID):
        self._write_to_user_value(userID, k_chatid, chatID)
        return
        
    # Check if this user has started a private chat with bot
    def is_registered(self, userID):
        user = self.udm.get_user(userID)
        print("REGISTERED? User: ", user)
        registered_flag = (k_fac in user and k_chatid in user)
        return registered_flag


    def get_chatID(self, userID):
        return self._get_user_value(userID, k_chatid)
    
    def user_exists(self, userID):
        return self.udm.user_exists(userID)

    # FACULTY methods
    def add_faculty(self, userID, fac):
        self._write_to_user_value(userID, k_fac, fac)
    
    def get_faculty(self, userID):
        return self._get_user_value(userID, k_fac)

    def add_year(self, userID, year):
        self._write_to_user_value(userID, k_yr, year)
    
    def get_year(self, userID):
        return self._get_user_value(userID, k_yr)

    # MODULE methods
    def add_senior_modules(self, userID, senior_mods):
        self._write_to_user_value(userID, k_snrmods, senior_mods)
        info = {
                "grade": "A-",
                "semester": "18/19 Sem 1"
            }
        for modcode in senior_mods:
            self.udm.write_user_to_module(modcode, userID, info)
        return

    def get_senior_modules(self, uid):
        return self._get_user_value(uid, k_snrmods)

    def get_profile_text(self, userID):
        template = "Faculty: {}\nYear of study: {}\nAnswering questions from the following modules:{}"
        fac = self.get_faculty(userID)
        year = self.get_year(userID)
        modules = self.get_senior_modules(userID)
        modules_text = ""
        if modules == False:
            modules_text = "\nNone"
        else:
            for k in list(modules.keys()):
                modules_text = modules_text + "\n" + k
            
        final = template.format(fac, year, modules_text)
        return final

    # Returns a list of chat ids 
    def get_chatids_for_mod(self, module_code):
        senior_chat_ids = []
        mod_data = self.udm.get_module(module_code)
        senior_userids = list(mod_data.keys())
        for suid in senior_userids:
            if not self._is_dnd(suid):
                senior_chat_ids.append(self.get_chatID(suid))
        return senior_chat_ids

    def _is_dnd(self, senior_uid):
        return senior_uid in self.dnd_table

    def toggle_dnd(self, senior_uid):
        if senior_uid in self.dnd_table:
            # Turn off
            self.dnd_table.pop(senior_uid)
        else:
            # Turn on
            self.dnd_table[senior_uid] = 1

        

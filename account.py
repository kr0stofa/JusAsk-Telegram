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
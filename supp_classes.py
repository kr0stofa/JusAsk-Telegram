import datetime as dt
import re

from datetime import datetime



class User:
    def __init__(self, telegram_user):
        self.tele_user = telegram_user

    

mods = False

class Junior(User):
    def get_mods(self):
        return mods

class Senior(User):
    def get_mods(self):
        return mods
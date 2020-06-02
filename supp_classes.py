import datetime as dt
import re

from datetime import datetime

class Remindo:
    def __init__(self, initating_user, datetime, name = ""):
        self.date, self.time = self._split_datetime(datetime)
        self.initating_user = initating_user
        self.name = ""

    def _split_datetime(self, dt):
        return (date, time)

    def toString(self):
        return "<Remindo> On %s At %s Started by: %s" % (self.date, self.time, self.initating_user)  


def parse_datestring(ds):
    ddmmm_pattern = "[0-9]+ 3*[a-Z]"
    digits = "[0-9]"
    month_map = {
        "Jan":1,
        "Feb":2,
        "Mar":3,
        "Apr":4,
        "May":5,
        "Jun":6,
        "Jul":7,
        "Aug":8,
        "Sep":9,
        "Oct":10,
        "Nov":11,
        "Dec":12,
    }
    # Cut to "DD MMM"
    if re.search(ddmmm_pattern, ds):
        daymonth_obj = datetime.strptime(ds, '%d %b') # 31 Jan
    elif re.search(mmmdd_pattern, ds):
        daymonth_obj = datetime.strptime(ds, '%b %d') # Jan 31    

    curr_year = datetime.today().year
    final_date = datetime.date(curr_year, daymonth_obj.month, daymonth_obj.day)

    return final_date
        

ss = "15 Jun"
dt_obj = datetime.strptime(ss, '%d %b')    

curr_year = datetime.today().year
final_date = dt.date(curr_year, dt_obj.month, dt_obj.day)

print(dt_obj)

print(final_date)

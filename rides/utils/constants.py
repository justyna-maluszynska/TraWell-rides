import datetime

ACTUAL_RIDES_ARGS = {"is_cancelled": False, "start_date__gt": datetime.datetime.today() + datetime.timedelta(hours=1)}

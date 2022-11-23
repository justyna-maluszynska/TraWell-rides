import scripts.create_cities
import scripts.create_rides
import scripts.create_recurrent_rides


RIDES_AMOUNT_WITH_THE_SAME_CITY_TO = 100
RECURRENT_RIDES_WITH_THE_SAME_CITY_TO = 2

scripts.create_cities.create()
scripts.create_rides.create(RIDES_AMOUNT_WITH_THE_SAME_CITY_TO)
scripts.create_recurrent_rides.create(RECURRENT_RIDES_WITH_THE_SAME_CITY_TO)

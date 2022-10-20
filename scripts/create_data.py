import scripts.create_vehicles
import scripts.create_users
import scripts.create_cities
import scripts.create_rides

VEHICLES_AMOUNT = 20
USERS_AMOUNT = 20
RIDES_AMOUNT_WITH_THE_SAME_CITY_TO = 100

scripts.create_vehicles.create(VEHICLES_AMOUNT)
scripts.create_users.create(USERS_AMOUNT)
scripts.create_cities.create()
scripts.create_rides.create(RIDES_AMOUNT_WITH_THE_SAME_CITY_TO)

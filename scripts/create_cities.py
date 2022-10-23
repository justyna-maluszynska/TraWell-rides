from cities.factories import CityFactory

cities = [
    {'name': 'Wrocław', 'county': 'Wrocław', 'state': 'Lower Silesian Voivodeship', 'lat': 51.126308, 'lng': 16.978201},
    {'name': 'Warszawa', 'county': 'Warszawa', 'state': 'Masovian Voivodeship', 'lat': 52.233719, 'lng': 21.071409},
    {'name': 'Łódź', 'county': 'Łódź', 'state': 'Łódź Voivodeship', 'lat': 51.77306, 'lng': 19.47838},
    {'name': 'Zakopane', 'county': 'Zakopane', 'state': 'Lesser Poland Voivodeship', 'lat': 49.275791, 'lng': 19.96928},
    {'name': 'Katowice', 'county': 'Katowice', 'state': 'Silesian Voivodeship', 'lat': 50.21373, 'lng': 19.00589},
    {'name': 'Syców', 'county': 'Syców', 'state': 'Lower Silesian Voivodeship', 'lat': 51.303261, 'lng': 17.73263},
    {'name': 'Ełk', 'county': 'Ełk', 'state': 'Warmian-Masurian Voivodeship', 'lat': 53.823959, 'lng': 22.361919},
    {'name': 'Olecko', 'county': 'gmina Olecko', 'state': 'Warmian-Masurian Voivodeship', 'lat': 54.03606,
     'lng': 22.501789},
    {'name': 'Oleśnica', 'county': 'Oleśnica', 'state': 'Lower Silesian Voivodeship', 'lat': 51.210239,
     'lng': 17.38295},
    {'name': 'Stegna', 'county': 'Stegna', 'state': 'Pomeranian Voivodeship', 'lat': 54.29821, 'lng': 19.040609},
    {'name': 'Wielka Lipa', 'county': 'Oborniki Śląskie', 'state': 'Lower Silesian Voivodeship', 'lat': 51.317039,
     'lng': 16.85873},
    {'name': 'Grzybki', 'county': 'Warta', 'state': 'Łódź Voivodeship', 'lat': 51.72723, 'lng': 18.604321},
    {'name': 'Rypin', 'county': 'Rypin', 'state': 'Kuyavian-Pomeranian Voivodeship', 'lat': 53.062962,
     'lng': 19.419331},
    {'name': 'Borucino', 'county': 'Połczyn-Zdrój', 'state': 'West Pomeranian Voivodeship', 'lat': 53.75692,
     'lng': 16.030861},
    {'name': 'Gryfino', 'county': 'Gryfino', 'state': 'West Pomeranian Voivodeship', 'lat': 53.256248, 'lng': 14.49146},
    {'name': 'Konin', 'county': 'Konin', 'state': 'Greater Poland Voivodeship', 'lat': 52.255901, 'lng': 18.26787},
    {'name': 'Kielce', 'county': 'Kielce', 'state': 'Świętokrzyskie Voivodeship', 'lat': 50.854038, 'lng': 20.609909},
    {'name': 'Radom', 'county': 'Radom', 'state': 'Masovian Voivodeship', 'lat': 51.41716, 'lng': 21.16095},
    {'name': 'Janczyce', 'county': 'gmina Baćkowice', 'state': 'Świętokrzyskie Voivodeship', 'lat': 50.762051,
     'lng': 21.2372},
    {'name': 'Częstochowa', 'county': 'Częstochowa', 'state': 'Silesian Voivodeship', 'lat': 50.808998,
     'lng': 19.124411}]


def create():
    for city in cities:
        name = city['name']
        county = city['county']
        state = city['state']
        lat = city['lat']
        lng = city['lng']
        CityFactory(name=name, county=county, state=state, lat=lat, lng=lng)

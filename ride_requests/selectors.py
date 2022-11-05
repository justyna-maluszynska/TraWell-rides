from utils.utils import filter_rides_by_cities, filter_by_decision


def requests_list(request, queryset, rides, decision: str, filters: dict):
    rides = filter_rides_by_cities(request, queryset=rides)

    queryset = queryset.filter(ride__in=list(rides), **filters)
    requests = filter_by_decision(decision, queryset)
    return requests

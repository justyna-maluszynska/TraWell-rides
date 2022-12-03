from users.models import User
from vehicles.models import Vehicle


def create_user(message):
    is_private = True if message['user_type'] == 'private' else False
    message['private'] = is_private
    user, _ = User.objects.update_or_create(user_id=message['user_id'], defaults=message)
    return user


def create_vehicle(message):
    user_data = message.pop('user')
    user, _ = create_user(user_data)
    vehicle, _ = Vehicle.objects.update_or_create(vehicle_id=message['vehicle_id'], user=user, defaults=message)
    return vehicle


def delete_vehicle(message):
    try:
        vehicle = Vehicle.objects.get(vehicle_id=message['vehicle_id'])
        vehicle.delete()
    except Vehicle.DoesNotExist:
        pass

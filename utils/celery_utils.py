from users.models import User
from vehicles.models import Vehicle


def create_user(message):
    is_private = True if message['user_type'] == 'private' else False
    message['private'] = is_private
    user, _ = User.objects.update_or_create(user_id=message['user_id'], defaults={'first_name': message['first_name'],
                                                                                  'last_name': message["last_name"],
                                                                                  'email': message["email"],
                                                                                  'avatar': message['avatar'],
                                                                                  'private': True if message[
                                                                                                         'user_type'] == 'private' else False,
                                                                                  'avg_rate': message['avg_rate']})
    return user


def create_vehicle(message):
    user_data = message.pop('user')
    user = create_user(user_data)
    vehicle, _ = Vehicle.objects.update_or_create(vehicle_id=message['vehicle_id'], user=user,
                                                  defaults={'make': message['make'],
                                                            'model': message['model'],
                                                            'color': message['color'],
                                                            })
    return vehicle


def delete_vehicle(message):
    try:
        vehicle = Vehicle.objects.get(vehicle_id=message['vehicle_id'])
        vehicle.delete()
    except Vehicle.DoesNotExist:
        pass

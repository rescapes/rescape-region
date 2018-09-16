from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from rescape_python_helpers import ramda as R

# The User schema is defined in rescape-graphene, but we still need sample data

sample_users = [
    dict(username="lion", first_name='Simba', last_name='The Lion',
                                  password=make_password("roar", salt='not_random')),
    dict(username="cat", first_name='Felix', last_name='The Cat',
                                  password=make_password("meow", salt='not_random'))
]


def create_sample_user(user_dict):
    # Save the region with the complete data
    user = get_user_model()(**user_dict)
    user.save()
    return user


def create_sample_users():
    # Deletes any users and then creates samples
    delete_sample_users()
    return R.map(create_sample_user, sample_users)


def delete_sample_users():
    get_user_model().objects.all().delete()
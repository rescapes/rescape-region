=====
Rescape-Region
=====

A Django app to support limiting users by geographic region

Quick start
-----------

1. Add "rescape-region" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'rescape-region',
    ]

2. Include the polls URLconf in your project urls.py like this::

    path('rescape-region/', include('regional.urls')),

3. Run `python manage.py migrate` to create the rescape-region models.

## Installation

Create a virtual environment using
```bash
mkdir ~/.virtualenvs
python3 -m venv ~/.virtualenvs/rescape-region
Activate it
source ~/.virtualenvs/rescape-region/bin/activate
```

#### Install requirements
Install requirements with latest versions
```bash
# pur tries to use python 2, so use pip-upgrade instead
pur -r requirements.txt && $VIRTUAL_ENV/bin/pip3 install --no-cache-dir  --upgrade -r requirements.txt
```

Add the following to the bottom $VIRTUAL_ENV/bin/activate to setup the PYTHONPATH.
Replace the path with your code directory

```bash
export RESCAPE_REGION_BASE_DIR=/Users/andy/code/rescape-region
export RESCAPE_REGION_PROJECT_DIR=$RESCAPE_REGION_BASE_DIR/rescape-region
export PYTHONPATH=.:$RESCAPE_REGION_BASE_DIR:$RESCAPE_REGION_PROJECT_DIR
```

## Build

Update the version in setup.py
Run to generate build:
Update the version with bumpversion, which can't seem to look it up itself but updates setup.py

install wheel and bumpversion if needed
```
pip3 install wheel
pip3 install bumpversion
```

```bash
git commit . -m "Version update" && git push
bumpversion --current-version {look in setup.py} patch setup.py
python3 setup.py clean sdist bdist_wheel
```

To distribute to pypi site:
Upload package:

```bash
twine upload dist/*
```

All at once:
```bash
git commit . -m "Version update" && git push && bumpversion --current-version {look in setup.py} patch setup.py && python3 setup.py clean sdist bdist_wheel && twine upload dist/*
# Without commit
bumpversion --current-version {look in setup.py} patch setup.py && python3 setup.py clean sdist bdist_wheel && twine upload dist/*
```

For setup of testpypi see ~/.pypirc or create one according to the testpypi docs:
e.g.:
[distutils]
index-servers=
    pypi
    testpypi

[testpypi]
repository: https://test.pypi.org/legacy/
username: your username for pypi.org

## Running tests
Create a postgres database rescape_region
# Login to psql:
CREATE DATABASE rescape_region;
CREATE USER test_user WITH PASSWORD 'test';
GRANT ALL PRIVILEGES ON DATABASE rescape_region to test_user;
# Give Superuser permission to create test databasees
ALTER ROLE test_user SUPERUSER;

# Migrate the database
./manage migrate

# Create a Django user test with pw testpass
 ./manage.py createsuperuser
 # or
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('test', 'test@nowhere.man', 'testpass')" | ./manage.py shell

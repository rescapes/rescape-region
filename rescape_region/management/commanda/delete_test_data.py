import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from safedelete.models import HARD_DELETE

from rescape_region.model_helpers import get_project_model
from rescape_region.models import Location

from rescape_python_helpers import ramda as R
log = logging.getLogger('info')


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass


    def handle(self, *args, **options):
        """
        Hard deletes soft deleted 'test' user data
        """

        user = get_user_model().objects.get(username='test')
        delete_projects = get_project_model().objects.all_with_deleted().filter(user=user)
        delete_projects.delete(HARD_DELETE)
        log.info(f'Deleted {R.length(delete_projects)} projects')

        Location.objects.all_with_deleted().filter(location__name__startswith='Hillsborough').delete(HARD_DELETE)

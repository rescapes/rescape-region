from django.db import models
from reversion.models import Version
from rescape_python_helpers import ramda as R

import logging

logger = logging.getLogger('rescape_region')


class RevisionModelMixin(models.Model):

    @property
    def initial_version(self):
        # The initial version object
        return R.last(list(Version.objects.get_for_object(self)))

    @property
    def latest_version(self):
        # The latest version object
        return R.head(list(Version.objects.get_for_object(self)))

    @property
    def instance_version(self):
        """
            Uses self._version if defined, else assumes the lastest version
        :return:
        """
        return self._version if R.has('_version', self) else self.latest_version

    @property
    def created_at(self):
        # Get the initial version's date_created
        # If the model instance has a legacy field date_created_unrevisioned, use that instead
        if hasattr(self, 'created_at_unrevisioned'):
            return self.created_at_unrevisioned

        return self.initial_version.revision.date_created if \
            self.pk and self.initial_version else None

    @property
    def updated_at(self):
        # Get the current version's (defaults to latest version) revision's create_date
        return self.instance_version.revision.date_created if self.pk and self.instance_version else None

    @property
    def version_number(self):
        """
            There is no version number, only a revision number. Query and order by revision_id ascending to get
            a 1-based index
        :return:
        """
        if not self.instance_version:
            return None

        try:
            return list(Version.objects.get_for_object(self).order_by('revision_id')).index(self.instance_version) + 1
        except Exception as e:
            logger.warning(e)
            return -1

    @property
    def revision_id(self):
        """
            There is no version number, only a revision number. So use count to show the version
        :return:
        """
        return self.instance_version.revision.id if self.pk and self.instance_version else None

    class Meta:
        abstract = True

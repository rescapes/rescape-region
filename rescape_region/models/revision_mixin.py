from django.db import models
from reversion.models import Version
from rescape_python_helpers import ramda as R


class RevisionModelMixin(models.Model):
    @property
    def created_at(self):
        # Get the first version's create date.
        # If the model instance has a legacy field date_created_unrevisioned, use that instead
        if hasattr(self, 'created_at_unrevisioned'):
            return self.created_at_unrevisioned

        return R.last(list(Version.objects.get_for_object(self))).revision.date_created if \
            not self.pk else None

    @property
    def latest_version(self):
        # The latest version object
        return R.head(list(Version.objects.get_for_object(self)))

    @property
    def updated_at(self):
        # Get the current version's revision's create_date
        return self.latest_version.revision.date_created if self.pk else None

    @property
    def version_number(self):
        """
            There is no version number, only a revision number. So use count to show the version
        :return:
        """
        return Version.objects.get_for_object(self).count()

    @property
    def revision_id(self):
        """
            There is no version number, only a revision number. So use count to show the version
        :return:
        """
        return Version.objects.get_for_object(self).revsion.id


    class Meta:
        abstract = True

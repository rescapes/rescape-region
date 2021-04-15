import reversion
from django.db.models import JSONField
from django.db.models import CharField
from safedelete.models import SafeDeleteModel

from rescape_region.model_helpers import settings_data_default
from rescape_region.models.revision_mixin import RevisionModelMixin


@reversion.register()
class Settings(SafeDeleteModel, RevisionModelMixin):
    """
        Global settings. This is a single instance class at the moment but can be expanded to handle different
        servers and other global settings that need to be customized by geographic region or similar.
        No user settings are stored here, that is all stored in UserState
    """
    # Unique human readable identifier
    key = CharField(max_length=50, unique=True, null=False)
    data = JSONField(null=False, default=settings_data_default)

    class Meta:
        app_label = "rescape_region"

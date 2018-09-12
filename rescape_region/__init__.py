# TODO this is needed for the package but causes problems when running Django
# So comment out when doing migrations, etc
from .models import (
    UserState,
    Feature,
    Region
)

__all__ = [
    'models.feature',
    'models.region',
    'models.user_state',
]

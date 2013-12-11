from django.db import models
from rapidsms.models import Backend
from django.contrib.auth.models import User

class UserBackend(models.Model):
    """
    Represents which backends a user can create polls against
    """
    user = models.ForeignKey(User, related_name='backends')
    backend = models.ForeignKey(Backend, related_name='users')

    class Meta:
        unique_together = ('user', 'backend')

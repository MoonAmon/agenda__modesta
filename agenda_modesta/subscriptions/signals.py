from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import Subscritor


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_subscritor(sender, instance, created, **kwargs):
    """
    Automatically create a Subscritor when a new User is created.
    """
    if created:
        Subscritor.objects.create(usuario=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_subscritor(sender, instance, **kwargs):
    """
    Save the Subscritor when the User is saved.
    """
    if hasattr(instance, 'subscritor'):
        instance.subscritor.save()


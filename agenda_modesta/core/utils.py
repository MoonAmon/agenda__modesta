from agenda_modesta.subscriptions.models import Subscritor


def get_user_subscritor(user):
    """
    Get or create a Subscritor for the given user.
    This handles the case where a user exists but doesn't have an associated Subscritor.
    """
    try:
        return user.subscritor
    except Subscritor.DoesNotExist:
        return Subscritor.objects.create(usuario=user)


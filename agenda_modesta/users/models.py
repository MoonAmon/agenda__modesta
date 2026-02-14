from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CharField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Default custom user model for Agenda Modesta.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("professor", "Professor"),
    )

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]

    # --- novos campos ---
    nome_completo = models.CharField(
        _("Nome completo"), max_length=255, blank=True,
    )
    custo_horario_padrao = models.DecimalField(
        _("Custo horário padrão"),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )
    logo_empresa = models.ImageField(
        _("Logo da empresa"),
        upload_to="logos/",
        null=True,
        blank=True,
    )
    role = models.CharField(
        _("Papel"),
        max_length=20,
        choices=ROLE_CHOICES,
        default="professor",
    )
    ativo = models.BooleanField(_("Ativo"), default=True)

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})

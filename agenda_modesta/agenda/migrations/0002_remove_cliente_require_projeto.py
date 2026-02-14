import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("agenda", "0001_initial"),
    ]

    operations = [
        # Remove the cliente FK
        migrations.RemoveField(
            model_name="agenda",
            name="cliente",
        ),
        # Make projeto non-nullable (all existing rows already have a value)
        migrations.AlterField(
            model_name="agenda",
            name="projeto",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="agendamentos",
                to="projects.projeto",
            ),
        ),
    ]

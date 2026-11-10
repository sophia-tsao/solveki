from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0026_deck_per_assignment'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentassignment',
            name='finish_on',
            field=models.DateField(blank=True, null=True),
        ),
    ]

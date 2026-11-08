from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0023_dailydeck_attempts'),
    ]

    operations = [
        migrations.AddField(
            model_name='problemreport',
            name='steps',
            field=models.JSONField(blank=True, default=list),
        ),
    ]

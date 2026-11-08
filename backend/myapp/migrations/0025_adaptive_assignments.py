from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0024_problemreport_steps'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='allow_late',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='studentassignment',
            name='cards_needed',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='studentassignment',
            name='completion_pct',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='studentassignment',
            name='max_reached',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='studentassignment',
            name='late',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='dailytopicgrade',
            name='snapshot_due_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='dailytopicgrade',
            name='early',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='dailytopicgrade',
            name='floor_interval',
            field=models.IntegerField(default=0),
        ),
    ]

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0019_fill_topic_learn_more_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentassignment',
            name='cards_answered',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='studentassignment',
            name='completed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

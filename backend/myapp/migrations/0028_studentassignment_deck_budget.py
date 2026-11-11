from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0027_studentassignment_finish_on'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentassignment',
            name='deck_answered',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='studentassignment',
            name='review_answered',
            field=models.IntegerField(default=0),
        ),
    ]

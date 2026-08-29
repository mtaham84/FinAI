from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="emailverificationtoken",
            name="code_hash",
            field=models.CharField(max_length=256, default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="emailverificationtoken",
            name="attempt_count",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="emailverificationtoken",
            name="resend_count",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="emailverificationtoken",
            name="window_started_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="emailverificationtoken",
            name="locked_until",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

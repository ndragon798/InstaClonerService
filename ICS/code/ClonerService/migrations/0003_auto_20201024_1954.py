# Generated by Django 3.1.2 on 2020-10-25 00:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ClonerService', '0002_logininfo_cookie'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logininfo',
            name='cookie',
            field=models.TextField(),
        ),
    ]

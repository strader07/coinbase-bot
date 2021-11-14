# Generated by Django 2.2.10 on 2021-03-17 04:13

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('currency', models.CharField(max_length=100, null=True)),
                ('balance', models.CharField(max_length=100, null=True)),
                ('hold', models.CharField(max_length=100, null=True)),
                ('available', models.CharField(max_length=100, null=True)),
                ('can_trade', models.BooleanField(default=False, null=True)),
            ],
        ),
    ]

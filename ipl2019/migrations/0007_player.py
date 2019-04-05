# Generated by Django 2.1.5 on 2019-04-05 05:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ipl2019', '0006_auto_20190404_1849'),
    ]

    operations = [
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(max_length=100)),
                ('cost', models.PositiveIntegerField(default=0)),
                ('base', models.PositiveIntegerField(default=0)),
                ('team', models.CharField(blank=True, max_length=3)),
                ('country', models.TextField(max_length=100)),
                ('type', models.CharField(blank=True, max_length=12)),
                ('score', models.DecimalField(decimal_places=1, default=0, max_digits=6)),
            ],
            options={
                'ordering': ['-score'],
            },
        ),
    ]

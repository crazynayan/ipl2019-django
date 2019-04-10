# Generated by Django 2.1.5 on 2019-04-09 08:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ipl2019', '0012_bid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='playerinstance',
            name='status',
            field=models.CharField(choices=[('Available', 'Available'), ('Purchased', 'Purchased'), ('Bidding', 'Bidding'), ('Unsold', 'Unsold')], default='Available', max_length=10),
        ),
    ]
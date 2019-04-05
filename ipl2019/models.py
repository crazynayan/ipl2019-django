from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.TextField(max_length=100, default='name')
    points = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    balance = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-points']
        permissions = (
            ("auctioneer", "Auctioneer"),
            ("can_play_ipl2019", "Can play IPL 2019"),
        )


@receiver(post_save, sender=User)
def create_user_member(sender, instance, created, **kwargs):
    if created:
        Member.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_member(sender, instance, **kwargs):
    if hasattr(instance, 'Member'):
        instance.member.save()


class Player(models.Model):
    name = models.TextField(max_length=100)
    cost = models.PositiveIntegerField(default=0)
    base = models.PositiveIntegerField(default=0)
    team = models.CharField(max_length=4, blank=True)
    country = models.TextField(max_length=100)
    type = models.CharField(max_length=12, blank=True)
    score = models.DecimalField(max_digits=6, decimal_places=1, default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-score']


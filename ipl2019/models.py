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


@receiver(post_save, sender=User)
def create_user_member(sender, instance, created, **kwargs):
    if created:
        Member.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_member(sender, instance, **kwargs):
    if hasattr(instance, 'Member'):
        instance.member.save()


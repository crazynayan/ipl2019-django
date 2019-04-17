from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.TextField(max_length=100, default='name')
    balance = models.PositiveIntegerField(default=0)
    color = models.TextField(max_length=20, default='black')
    bgcolor = models.TextField(max_length=20, default='white')

    def __str__(self):
        return self.name

    class Meta:
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
    RATIO = 5.91
    name = models.TextField(max_length=100)
    cost = models.PositiveIntegerField(default=0)
    iplbase = models.PositiveIntegerField(default=0)
    team = models.ForeignKey('Team', on_delete=models.SET_NULL, null=True, related_name='players')
    country = models.TextField(max_length=100)
    type = models.CharField(max_length=12, blank=True)
    score = models.DecimalField(max_digits=6, decimal_places=1, default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-score']

    @property
    def base(self):
        return max(self.iplbase, round(float(self.score) * self.RATIO))


class PlayerInstance(models.Model):
    number = models.PositiveIntegerField(unique=True)
    player = models.ForeignKey('Player', on_delete=models.CASCADE, related_name='playerinstances')
    member = models.ForeignKey('Member', on_delete=models.SET_NULL, null=True, related_name='playerinstances')
    AVAILABLE = 'Available'
    PURCHASED = 'Purchased'
    BIDDING = 'Bidding'
    UNSOLD = 'Unsold'
    STATUS = (
        (AVAILABLE, 'Available'),
        (PURCHASED, 'Purchased'),
        (BIDDING, 'Bidding'),
        (UNSOLD, 'Unsold'),
    )
    status = models.CharField(max_length=10, choices=STATUS, default='Available')
    price = models.PositiveIntegerField(blank=True, default=0)

    def __str__(self):
        return f'{self.player} ({self.number})'


class Bid(models.Model):
    NO_BALANCE = -2
    PASS = -1
    OWNED = -3
    amount = models.IntegerField(blank=True, default=0)
    player_instance = models.ForeignKey('PlayerInstance', on_delete=models.CASCADE, related_name='bids')
    member = models.ForeignKey('Member', on_delete=models.SET_NULL, null=True, related_name='bids')

    def __str__(self):
        return f'{self.player_instance} - {self.member} - {self.amount}'


class Team(models.Model):
    name = models.CharField(max_length=4, null=True)
    full_name = models.CharField(max_length=30, null=True)

    def __str__(self):
        return self.name


class Match(models.Model):
    name = models.CharField(max_length=10, null=True)
    date = models.DateField()
    teams = models.ManyToManyField('Team', through='TeamMatch', related_name='matches')

    def __str__(self):
        return self.name


class TeamMatch(models.Model):
    team = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='team_matches')
    match = models.ForeignKey('Match', on_delete=models.CASCADE, related_name='team_matches')

    def __str__(self):
        return f'{self.team} in {self.match} match.'

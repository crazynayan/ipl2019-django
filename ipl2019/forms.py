from django import forms
from django.core.exceptions import ValidationError
from ipl2019.models import Bid


class BidForm(forms.Form):
    bid = forms.IntegerField(help_text='Enter a bid value for the player')

    def __init__(self, *args, **kwargs):
        self.player_instance = kwargs.pop('player_instance')
        self.member = kwargs.pop('member')
        super(BidForm, self).__init__(*args, **kwargs)

    def clean_bid(self):
        amount = self.cleaned_data['bid']
        if Bid.objects.filter(member=self.member).filter(player_instance=self.player_instance):
            raise ValidationError('You have already bid on this player.')
        if self.member.playerinstances.filter(player=self.player_instance.player).exists():
            raise ValidationError('You already own this player. You cannot bid for player already owned')
        if 'pass_bid' in self.data:
            amount = Bid.PASS
        else:
            if amount < self.player_instance.player.base:
                raise ValidationError('Bid cannot be less than the base value.')
            if amount > self.member.balance:
                raise ValidationError('You cannot bid more than your balance.')
        return amount


class PlayerRemovalForm(forms.Form):
    player_removal = forms.BooleanField(label='Enable Player Removal', required=False)

    def clean_player_removal(self):
        removal_switch = self.cleaned_data['player_removal']
        return removal_switch

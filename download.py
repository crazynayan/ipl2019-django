import json
from typing import List

from ipl2019.models import Member, PlayerInstance, Bid

pis: List[PlayerInstance] = PlayerInstance.objects.all()


def dm():
    members: List[Member] = Member.objects.all()
    members: list = [{'user': m.user.username, 'name': m.name, 'balance': m.balance, 'color': m.color,
                      'bg_color': m.bgcolor, 'points': float(sum(pi.player.score for pi in pis
                                                                 if pi.member and pi.member.name == m.name))}
                     for m in members]
    with open('members.json', 'w') as file:
        json.dump(members, file, indent=2)


def dpi():
    bids: List[Bid] = Bid.objects.all()
    players = [{'name': pi.player.name, 'price': pi.price, 'owner': pi.member.user.username if pi.member else None,
                'cost': pi.player.cost, 'base': pi.player.iplbase, 'country': pi.player.country,
                'type': pi.player.type, 'score': float(pi.player.score), 'team': pi.player.team.name,
                'bids': {b.member.user.username: b.amount for b in bids if b.player_instance.id == pi.id},
                'bid_order': next((b.id for b in bids if b.player_instance.id == pi.id), 0),
                } for pi in pis]
    with open('players.json', 'w') as file:
        json.dump(players, file, indent=2)


def db():
    bids: List[Bid] = Bid.objects.all()
    bids: list = [{'player_id': b.player_instance.id, 'player': b.player_instance.name, 'user': b.member.user.username,
                   'amount': b.amount} for b in bids]
    with open('bids.json', 'w') as file:
        json.dump(bids, file, indent=2)

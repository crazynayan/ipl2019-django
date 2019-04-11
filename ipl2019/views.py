import csv
import random

from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import permission_required
from django.contrib import messages
from django.db.models import Sum
from .models import Member, Player, PlayerInstance, Bid
from .forms import BidForm, PlayerRemovalForm


@permission_required('ipl2019.can_play_ipl2019')
def member_list(request):
    template = "ipl2019/member_list.html"
    members = Member.objects.annotate(pts=Sum('playerinstances__player__score')).order_by('-pts')
    context = {
        'member_list': members,
    }
    return render(request, template, context)


@permission_required('ipl2019.can_play_ipl2019')
def player_list(request):
    template = "ipl2019/player_list.html"
    context = {
        'player_list': Player.objects.all(),
    }
    return render(request, template, context)


@permission_required('ipl2019.can_play_ipl2019')
def my_player(request):
    template = "ipl2019/my_player_list.html"
    try:
        me = Member.objects.get(user=request.user.id)
        context = {
            'player_instances': PlayerInstance.objects.filter(member=me).order_by('-player__score'),
            'me': me,
            'type': 'my',
            'player_removal': settings.IPL2019_PLAYER_REMOVAL,
        }
    # Only the superuser will not have any ownership. So for superuser display all players.
    except ObjectDoesNotExist:
        context = {
            'player_instances': PlayerInstance.objects.all().order_by('number'),
            'type': 'all',
            'player_removal': settings.IPL2019_PLAYER_REMOVAL,
        }
    return render(request, template, context)


@permission_required('ipl2019.can_play_ipl2019')
def all_player(request):
    template = "ipl2019/my_player_list.html"
    context = {
        'player_instances': PlayerInstance.objects.all().order_by('number'),
        'type': 'all',
    }
    return render(request, template, context)


@permission_required('ipl2019.can_play_ipl2019')
def available_player(request):
    template = "ipl2019/my_player_list.html"
    try:
        me = Member.objects.get(user=request.user.id)
    except ObjectDoesNotExist:
        me = None
    context = {
        'player_instances':
            PlayerInstance.objects
            .filter(status__in=[PlayerInstance.AVAILABLE, PlayerInstance.UNSOLD, PlayerInstance.BIDDING])
            .order_by('-player__score', '-player__cost', 'player__name'),
        'me': me,
        'type': 'available',
        'player_removal': settings.IPL2019_PLAYER_REMOVAL,
    }
    return render(request, template, context)


@permission_required('ipl2019.can_play_ipl2019')
def bid_list(request):
    template = "ipl2019/bid_list.html"
    members_sorted = Member.objects.all().order_by('user__username')
    header = [member.user.username.upper() for member in members_sorted]
    try:
        bidding_player = PlayerInstance.objects.get(status=PlayerInstance.BIDDING)
        bids = Bid.objects.exclude(player_instance=bidding_player)
    except ObjectDoesNotExist:
        bids = Bid.objects.all()

    # bid_pivot has the following structure
    # bid_pivot = [
    #     {
    #         'player': 'Virat Kohli (1)',
    #         'members': [
    #             {
    #                 'username': 'AG',
    #                 'amount': 1000,
    #             },
    #             {
    #                 'username': 'VP',
    #                 'amount': 1200,
    #             },
    #         ],
    #     },
    #     {
    #         'player': 'Virat Kohli (2)',
    #         'members': [
    #             {
    #                 'username': 'AG',
    #                 'amount': 1100,
    #             },
    #             {
    #                 'username': 'NZ',
    #                 'amount': 1050,
    #             },
    #         ],
    #     },
    # ]
    bid_pivot = list()
    for bid in bids:
        member_bid = {
            'username': bid.member.user.username.upper(),
            'amount': max(0, bid.amount),
            'winner': False,
        }
        if bid.player_instance.member == bid.member:
            member_bid['winner'] = True
        try:
            player_bid = [bid_dict for bid_dict in bid_pivot if bid_dict['player'] == bid.player_instance][0]
            player_bid['members'].append(member_bid)
        except IndexError:
            player_bid = {
                'player': bid.player_instance,
                'members': list(),
            }
            player_bid['members'].append(member_bid)
            bid_pivot.append(player_bid)

    for player_bid in bid_pivot:
        player_bid['members'].sort(key=lambda member: member['username'])

    context = {
        'header': header,
        'player_bids': bid_pivot,
    }
    return render(request, template, context)


@permission_required('ipl2019.can_play_ipl2019')
def remove_player(request, pk):
    template = "ipl2019/confirmation.html"
    redirect = 'my_player_list'
    prompt = {
        'redirect': redirect,
    }
    try:
        player_instance = PlayerInstance.objects.get(pk=pk)
        confirmations = list()
        confirmations.append('Are you sure you want to remove this player?')
        confirmations.append(f'{player_instance.player.name} has scored {player_instance.player.score} points.')
        confirmations.append(f'You had purchased him for \u20B9 {player_instance.price} lakhs. ')
        confirmations.append(f'But if you sell him now his base price would be \u20B9 {player_instance.player.base} lakhs.')
        confirmations.append(f'He is a {player_instance.player.type} from {player_instance.player.team}.')
        confirmations.append(f'He was purchased by {player_instance.player.team} ' +
                             f'at \u20B9 {player_instance.player.cost} lakhs in the real auction.')
        if player_instance.member is not None:
            confirmations.append(f'Owner : {player_instance.member.name}')
        else:
            confirmations.append(f'Owner : Unsold')
        prompt['confirmations'] = confirmations
        prompt['player'] = player_instance
    except ObjectDoesNotExist:
        messages.error(request, "You cannot remove a player that does NOT exists.")
        return render(request, template, prompt)

    if request.method == "GET":
        return render(request, template, prompt)

    # Validate if the auctioneer has enabled removal of players.
    if not settings.IPL2019_PLAYER_REMOVAL:
        messages.error(request, 'Removal of players is disabled by auctioneer.')
        messages.error(request, 'Please contact auctioneer to enable player removal')
        return render(request, template, prompt)

    # Validate if the player is owned by anybody
    if player_instance.member is None:
        messages.error(request, f'{player_instance} is not owned by anybody.')
        messages.error(request, 'You can only release players that are owned.')
        return render(request, template, prompt)

    # Validate if the member owns the player.
    try:
        me = Member.objects.get(user=request.user.id)
        if player_instance.member.id != me.id:
            messages.error(request, "You cannot remove this player since you do NOT own him.")
            return render(request, template, prompt)
    # Only the superuser will not have any ownership. So allow superuser to remove any player.
    except ObjectDoesNotExist:
        pass

    # Validate if the member can release the player
    if player_instance.player.score >= 50:
        messages.error(request, f'{player_instance.player.name} has already scored {player_instance.player.score} points.')
        messages.error(request, 'You can only release players with less than 50 points.')
        return render(request, template, prompt)

    player_instance.member.balance += player_instance.price
    player_instance.member.save()

    player_instance.price = 0
    player_instance.status = PlayerInstance.AVAILABLE
    player_instance.member = None
    player_instance.save()

    return HttpResponseRedirect(reverse(redirect))


@permission_required('ipl2019.auctioneer')
def player_removal(request):
    template = "ipl2019/player_removal.html"
    prompt = {
        'removal': settings.IPL2019_PLAYER_REMOVAL
    }
    if request.method == "GET":
        removal_form = PlayerRemovalForm(initial={'player_removal': settings.IPL2019_PLAYER_REMOVAL})
        prompt['removal_form'] = removal_form
        return render(request, template, prompt)

    removal_form = PlayerRemovalForm(request.POST)
    if not removal_form.is_valid():
        prompt['removal_form'] = removal_form
        return render(request, template, prompt)

    settings.IPL2019_PLAYER_REMOVAL = removal_form.cleaned_data['player_removal']

    return HttpResponseRedirect(reverse('my_player_list'))


@permission_required('ipl2019.can_play_ipl2019')
def bid_player(request):
    template = "ipl2019/bid_player.html"
    prompt = {}
    try:
        me = Member.objects.get(user=request.user.id)
    except ObjectDoesNotExist:
        messages.error(request, "Superusers cannot bid.")
        return render(request, template, prompt)
    try:
        player_instance = PlayerInstance.objects.get(status=PlayerInstance.BIDDING)
    except ObjectDoesNotExist:
        messages.error(request, "There is no player enabled for bidding.")
        messages.error(request, "Try after some time or contact auctioneer to invite someone for bid.")
        return render(request, template, prompt)

    # Prepare current bid status
    bids = Bid.objects.filter(player_instance=player_instance)
    try:
        owner = bids.get(amount=Bid.OWNED).member
    except ObjectDoesNotExist:
        owner = None
    zero_bidders = [bid.member for bid in bids.filter(amount=Bid.NO_BALANCE)]
    bidders = [bid.member for bid in bids.exclude(amount__in=[Bid.OWNED, Bid.NO_BALANCE])]
    pending_bidders = Member.objects.exclude(id__in=bids.values_list('member', flat=True))

    prompt = {
        'member': me,
        'player_instance': player_instance,
        'owner': owner,
        'zero_bidders': zero_bidders,
        'bidders': bidders,
        'pending_bidders': pending_bidders,
    }

    # Validate if the member has already bid for this player
    # The bids can be of 4 types
    # 1. Auto bid of Bid.NO_BALANCE
    # 2. Auto bid of Bid.OWNED
    # 3. Bid.PASS
    # 4. Valid bid > base
    try:
        my_bid = Bid.objects.filter(player_instance=player_instance).get(member=me)
        if my_bid.amount == Bid.NO_BALANCE:
            messages.error(request, "You cannot bid for this player since you have insufficient balance.")
        elif my_bid.amount == Bid.OWNED:
            messages.error(request, f"You already own {player_instance.player}. You cannot bid for him again.")
        elif my_bid.amount == Bid.PASS:
            messages.error(request, "You have already decided to PASS this player.")
        else:
            messages.error(request, f"You have already made a bid of {my_bid.amount} lakhs for this player.")
        messages.error(request, "Please wait for bidding to complete & the next player to be invited.")
        return render(request, template, prompt)
    except ObjectDoesNotExist:
        pass

    if request.method == "GET":
        bid_form = BidForm(initial={'bid': player_instance.player.base},
                           member=me,
                           player_instance=player_instance)
        prompt['bid_form'] = bid_form
        return render(request, template, prompt)

    bid_form = BidForm(request.POST, member=me, player_instance=player_instance)
    if not bid_form.is_valid():
        prompt['bid_form'] = bid_form
        return render(request, template, prompt)

    bid = Bid(amount=bid_form.cleaned_data['bid'],
              member=me,
              player_instance=player_instance)
    bid.save()

    if is_bidding_complete(player_instance):
        winning_bids = Bid.objects.filter(player_instance=player_instance).order_by('-amount')
        if winning_bids[0].amount < player_instance.player.base:
            player_instance.status = PlayerInstance.UNSOLD
            player_instance.save()
        else:
            # If there is a tie (winner_count > 1) decide the winner randomly between all winners.
            # If there is no tie (winner_count = 1) then the winner_index will always be 0.
            winner_count = winning_bids.filter(amount=winning_bids[0].amount).count()
            winner_index = random.randrange(0, winner_count)
            winner = Member.objects.get(pk=winning_bids[winner_index].member.pk)

            player_instance.member = winner
            player_instance.price = max(winning_bids[1].amount, player_instance.player.base)
            player_instance.status = PlayerInstance.PURCHASED
            player_instance.save()
            winner.balance -= player_instance.price
            winner.save()

    return HttpResponseRedirect(reverse('available_player_list'))


@permission_required('ipl2019.auctioneer')
def invite_player(request, pk):
    template = "ipl2019/confirmation.html"
    redirect = 'available_player_list'
    try:
        player_instance = PlayerInstance.objects.get(pk=pk)
        confirmations = list()
        confirmations.append('Are you sure you want to invite this player for Bids?')
        confirmations.append(f'Name : {player_instance.player.name}')
        confirmations.append(f'Number : {player_instance.number}')
        confirmations.append(f'Score : {player_instance.player.score} points')
        confirmations.append(f'Team : {player_instance.player.team}')
        confirmations.append(f'Type : {player_instance.player.type}')
        confirmations.append(f'Base : {player_instance.player.base}')
        confirmations.append(f'Cost : {player_instance.player.cost}')
        if player_instance.member is not None:
            confirmations.append(f'Owner : {player_instance.member.name}')
        else:
            confirmations.append(f'Owner : Unsold')
        prompt = {
            'confirmations': confirmations,
            'player': player_instance,
            'redirect': redirect,
        }
    except ObjectDoesNotExist:
        messages.error(request, "You cannot invite a player that does NOT exists.")
        prompt = {
            'confirmations': ['This player does NOT exists.'],
            'player': None,
            'redirect': redirect,
        }
        return render(request, template, prompt)

    if request.method == "GET":
        return render(request, template, prompt)

    # Validate if the auctioneer has disabled removal of players.
    if settings.IPL2019_PLAYER_REMOVAL:
        messages.error(request, 'Removal of players is enabled by auctioneer.')
        messages.error(request, 'You cannot invite players for bids when the player removal is in progress.')
        return render(request, template, prompt)

    # Validate if the player is available.
    if player_instance.status != player_instance.AVAILABLE:
        messages.error(request, f'Status of {player_instance} is {player_instance.status}')
        messages.error(request, 'You can only invite available players.')
        return render(request, template, prompt)

    # ## Commented out the following scenarios because the AVAILABLE check takes care of it.
    # # Validate if the player is not owned by anybody
    # if player_instance.member is not None:
    #     messages.error(request, f'{player_instance} is owned by somebody.')
    #     messages.error(request, 'You can only release players that are not owned.')
    #     return render(request, template, prompt)
    #
    # # Validate if there are no bids for this player
    # if Bid.objects.filter(player_instance=player_instance).exists():
    #     messages.error(request, f'{player_instance} has already been invited for bids.')
    #     messages.error(request, 'You can only invites players one time.')
    #     return render(request, template, prompt)

    # Validate if another player is not under bidding
    if PlayerInstance.objects.filter(status=PlayerInstance.BIDDING).exists():
        messages.error(request, 'A Bidding is in progress. Please let it finish to invite another player.')
        return render(request, template, prompt)

    player_instance.status = PlayerInstance.BIDDING
    player_instance.save()

    # Auto Populate bids for members without sufficient balance
    # Auto Populate bids for member who already own this player
    try:
        owner = PlayerInstance.objects\
            .filter(player=player_instance.player)\
            .filter(status=PlayerInstance.PURCHASED)\
            .get()\
            .member
    except ObjectDoesNotExist:
        owner = None
    for member in Member.objects.all():
        if member.balance < player_instance.player.base:
            bid = Bid(member=member, player_instance=player_instance, amount=Bid.NO_BALANCE)
            bid.save()
        elif owner is not None and member == owner:
            bid = Bid(member=member, player_instance=player_instance, amount=Bid.OWNED)
            bid.save()
    if is_bidding_complete(player_instance):
        player_instance.status = PlayerInstance.UNSOLD
        player_instance.save()

    return HttpResponseRedirect(reverse(redirect))


def is_bidding_complete(player_instance):
    if player_instance.status != PlayerInstance.BIDDING:
        return False
    for member in Member.objects.all():
        if not Bid.objects.filter(member=member).filter(player_instance=player_instance).exists():
            return False
    return True


@permission_required('ipl2019.auctioneer')
def member_upload(request):
    template = "ipl2019/upload_csv.html"
    prompt = {
        'order': 'Order of member csv should be user, name, balance.',
    }

    if request.method == "GET":
        return render(request, template, prompt)

    file = request.FILES['file']

    if not file.name.endswith('.csv'):
        messages.error(request, "This file is not a .csv file.")
        return render(request, template, prompt)

    with open(file.name) as csv_file:
        csv_data = list(csv.reader(csv_file, delimiter=','))

    if csv_data[0] != ['user', 'name', 'balance']:
        messages.error(request, "The csv header is not in the proper format.")
        return render(request, template, prompt)

    for column in csv_data[1:]:
        try:
            user = User.objects.get(username=column[0])
            member = Member.objects.get(user=user.id)
            member.name = column[1]
            member.balance = column[2]
            member.save()
        except ObjectDoesNotExist:
            pass

    return HttpResponseRedirect(reverse('member_list'))


@permission_required('ipl2019.auctioneer')
def player_upload(request):
    template = "ipl2019/upload_csv.html"
    prompt = {
        'order': 'Order of player csv should be name, cost, base, team, country, type, score.',
    }

    if request.method == "GET":
        return render(request, template, prompt)

    file = request.FILES['file']

    if not file.name.endswith('.csv'):
        messages.error(request, "This file is not a .csv file.")
        return render(request, template, prompt)

    with open(file.name) as csv_file:
        csv_data = list(csv.reader(csv_file, delimiter=','))

    if csv_data[0] != ['name', 'cost', 'base', 'team', 'country', 'type', 'score']:
        messages.error(request, "The csv header is not in the proper format.")
        return render(request, template, prompt)

    for column in csv_data[1:]:
        _, created = Player.objects.update_or_create(
            defaults={
                'cost': column[1],
                'base': column[2],
                'team': column[3],
                'country': column[4],
                'type': column[5],
                'score': column[6],
                },
            name=column[0]
        )

    return HttpResponseRedirect(reverse('player_list'))


@permission_required('ipl2019.auctioneer')
def update_scores(request):
    template = "ipl2019/upload_csv.html"
    prompt = {
        'order': 'Order of scores csv should be player, score.',
    }

    if request.method == "GET":
        return render(request, template, prompt)

    file = request.FILES['file']

    if not file.name.endswith('.csv'):
        messages.error(request, 'This file is not a .csv file.')
        return render(request, template, prompt)

    with open(file.name) as csv_file:
        csv_data = list(csv.reader(csv_file, delimiter=','))

    if csv_data[0] != ['player', 'score']:
        messages.error(request, 'The csv header is not in the proper format.')
        return render(request, template, prompt)

    for column in csv_data[1:]:
        try:
            player = Player.objects.get(name=column[0])
            score = float(column[1])
            if player.score != score:
                player.score = score
                player.save()
        except ObjectDoesNotExist:
            pass
        except ValueError:
            pass

    return HttpResponseRedirect(reverse('member_list'))


@permission_required('ipl2019.auctioneer')
def player_ownership_upload(request):
    template = "ipl2019/upload_csv.html"
    prompt = {
        'order': 'Order of player ownership csv should be player, number, member, price.',
    }

    if request.method == "GET":
        return render(request, template, prompt)

    file = request.FILES['file']

    if not file.name.endswith('.csv'):
        messages.error(request, "This file is not a .csv file.")
        return render(request, template, prompt)

    with open(file.name) as csv_file:
        csv_data = list(csv.reader(csv_file, delimiter=','))

    if csv_data[0] != ['player', 'number', 'member', 'price']:
        messages.error(request, "The csv header is not in the proper format.")
        return render(request, template, prompt)

    for column in csv_data[1:]:
        try:
            player = Player.objects.get(name=column[0])
            user = str(column[2]).lower()
            if user == "base" or not User.objects.filter(username=user).exists():
                member = None
                status = PlayerInstance.AVAILABLE
            else:
                member = Member.objects.get(user=User.objects.get(username=user).id)
                status = PlayerInstance.PURCHASED

            _, created = PlayerInstance.objects.update_or_create(
                defaults={
                    'player': player,
                    'price': column[3],
                    'status': status,
                    'member': member,
                },
                number=column[1]
            )
        except ObjectDoesNotExist:
            pass

    return HttpResponseRedirect(reverse('all_player_list'))


@permission_required('ipl2019.auctioneer')
def reset(request):
    template = "ipl2019/confirmation.html"
    redirect = 'member_list'
    confirmations = list()
    confirmations.append('Are you sure you want to reset everything?')
    confirmations.append('This will reset member balances, players, player ownership and remove all bids.')
    confirmations.append('This uses member.csv, players.csv, player_ownership.csv.')
    confirmations.append('The reset will run for a few minutes. Don\'t close the page.')
    prompt = {
        'confirmations': confirmations,
        'redirect': redirect
    }

    if request.method == "GET":
        return render(request, template, prompt)

    with open('members.csv') as csv_file:
        member_data = list(csv.reader(csv_file, delimiter=','))

    if member_data[0] != ['user', 'name', 'balance']:
        messages.error(request, 'The member.csv header is not in the proper format.')
        messages.error(request, 'It needs to be in the order of user, name, balance')
        return render(request, template, prompt)

    with open('players.csv') as csv_file:
        players_data = list(csv.reader(csv_file, delimiter=','))

    if players_data[0] != ['name', 'cost', 'base', 'team', 'country', 'type']:
        messages.error(request, 'The players.csv header is not in the proper format.')
        messages.error(request, 'It needs to be in the order of name, cost, base, team, country, type')
        return render(request, template, prompt)

    with open('player_ownership.csv') as csv_file:
        own_data = list(csv.reader(csv_file, delimiter=','))

    if own_data[0] != ['player', 'number', 'member', 'price']:
        messages.error(request, 'The player_ownership.csv header is not in the proper format.')
        return render(request, template, prompt)

    # Upload Member Data
    for column in member_data[1:]:
        try:
            user = User.objects.get(username=column[0])
            member = Member.objects.get(user=user.id)
            member.name = column[1]
            member.balance = column[2]
            member.save()
        except ObjectDoesNotExist:
            pass

    # Upload Player Data
    for column in players_data[1:]:
        _, created = Player.objects.update_or_create(
            defaults={
                'cost': column[1],
                'base': column[2],
                'team': column[3],
                'country': column[4],
                'type': column[5],
            },
            name=column[0]
        )

    # Upload Player Ownership Data
    for column in own_data[1:]:
        try:
            player = Player.objects.get(name=column[0])
            user = str(column[2]).lower()
            if user == "base" or not User.objects.filter(username=user).exists():
                member = None
                status = PlayerInstance.AVAILABLE
            else:
                member = Member.objects.get(user=User.objects.get(username=user).id)
                status = PlayerInstance.PURCHASED

            _, created = PlayerInstance.objects.update_or_create(
                defaults={
                    'player': player,
                    'price': column[3],
                    'status': status,
                    'member': member,
                },
                number=column[1]
            )
        except ObjectDoesNotExist:
            pass

    # Delete all bids
    Bid.objects.all().delete()

    return HttpResponseRedirect(reverse(redirect))

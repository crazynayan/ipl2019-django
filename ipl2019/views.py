import csv

from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import permission_required
from django.contrib import messages
from django.db.models import Sum
from .models import Member, Player, PlayerInstance



@permission_required('ipl2019.can_play_ipl2019')
def member_view(request):
    template = "ipl2019/member_list.html"
    member_list = Member.objects.annotate(pts=Sum('playerinstances__player__score')).order_by('-pts')
    context = {
        'member_list': member_list,
    }
    return render(request, template, context)


@permission_required('ipl2019.can_play_ipl2019')
def player_view(request):
    template = "ipl2019/player_list.html"
    context = {
        'player_list': Player.objects.all(),
    }
    return render(request, template, context)


@permission_required('ipl2019.can_play_ipl2019')
def my_player_view(request):
    template = "ipl2019/my_player_list.html"
    try:
        me = Member.objects.get(user=request.user.id)
        context = {
            'player_instances': PlayerInstance.objects.filter(member=me).order_by('-player__score'),
            'me': me,
        }
    # Only the superuser will not have any ownership. So for superuser display all players.
    except ObjectDoesNotExist:
        context = {
            'player_instances': PlayerInstance.objects.all().order_by('number'),
        }
    return render(request, template, context)


@permission_required('ipl2019.can_play_ipl2019')
def all_player_view(request):
    template = "ipl2019/my_player_list.html"
    context = {
        'player_instances': PlayerInstance.objects.all().order_by('number'),
    }
    return render(request, template, context)


@permission_required('ipl2019.can_play_ipl2019')
def remove_player(request, pk):
    template = "ipl2019/confirmation.html"
    redirect = 'my_player_list'
    try:
        player_instance = PlayerInstance.objects.get(pk=pk)
        confirmations = ['Are you sure you want to remove this player?']
        confirmations.append(f'Name : {player_instance.player.name}')
        confirmations.append(f'Score : {player_instance.player.score} points')
        confirmations.append(f'Price : \u20B9 {player_instance.price} lakhs')
        confirmations.append(f'Team : {player_instance.player.team}')
        confirmations.append(f'Type : {player_instance.player.type}')
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
        messages.error(request, "You cannot remove a player that does NOT exists.")
        prompt = {
            'confirmations': ['This player does NOT exists.'],
            'player': None,
            'redirect': redirect,
        }
        return render(request, template, prompt)

    if request.method == "GET":
        return render(request, template, prompt)

    # Validate if the player is owned by anybody
    if player_instance.member is None:
        messages.error(request, f'{player_instance.player.name} is not owned by anybody.')
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

    # Validate if the auctioneer has enabled removal of players.

    player_instance.member.balance += player_instance.price
    player_instance.member.save()

    player_instance.price = 0
    player_instance.status = 'Available'
    player_instance.member = None
    player_instance.save()

    return HttpResponseRedirect(reverse(redirect))


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
                status = 'Available'
            else:
                member = Member.objects.get(user=User.objects.get(username=user).id)
                status = 'Purchased'

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

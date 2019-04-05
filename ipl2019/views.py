import csv

from django.shortcuts import render
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Member, Player, PlayerInstance
from django.contrib import messages


@permission_required('ipl2019.can_play_ipl2019')
def member_view(request):
    template = "ipl2019/member_list.html"
    context = {
        'member_list': Member.objects.all()
    }
    return render(request, template, context)


@permission_required('ipl2019.can_play_ipl2019')
def player_view(request):
    template = "ipl2019/player_list.html"
    context = {
        'player_list': Player.objects.all()
    }
    return render(request, template, context)


@permission_required('ipl2019.can_play_ipl2019')
def my_player_view(request):
    template = "ipl2019/my_player_list.html"
    try:
        me = Member.objects.get(user=request.user.id)
        context = {
            'player_instances': PlayerInstance.objects.filter(member=me).order_by('-player__score')
        }
    # Only the superuser will not have any ownership. So for superuser display all players.
    except ObjectDoesNotExist:
        context = {
            'player_instances': PlayerInstance.objects.all().order_by('number')
        }
    return render(request, template, context)


@permission_required('ipl2019.can_play_ipl2019')
def all_player_view(request):
    template = "ipl2019/my_player_list.html"
    context = {
        'player_instances': PlayerInstance.objects.all().order_by('number')
    }
    return render(request, template, context)


@permission_required('ipl2019.auctioneer')
def member_upload(request):
    template = "ipl2019/upload_csv.html"
    prompt = {
        'order': 'Order of member csv should be user, name, balance, points'
    }

    if request.method == "GET":
        return render(request, template, prompt)

    file = request.FILES['file']

    if not file.name.endswith('.csv'):
        messages.error(request, "This file is not a .csv file")
        return render(request, template, prompt)

    with open(file.name) as csv_file:
        csv_data = list(csv.reader(csv_file, delimiter=','))

    if csv_data[0] != ['user', 'name', 'balance', 'points']:
        messages.error(request, "The csv header is not in the proper format.")
        return render(request, template, prompt)

    for column in csv_data[1:]:
        try:
            a_user = User.objects.get(username=column[0])
            member = Member.objects.get(user=a_user.id)
            member.name = column[1]
            member.balance = column[2]
            member.points = column[3]
            member.save()
        except ObjectDoesNotExist:
            pass

    return HttpResponseRedirect(reverse('member_list'))


@permission_required('ipl2019.auctioneer')
def player_upload(request):
    template = "ipl2019/upload_csv.html"
    prompt = {
        'order': 'Order of player csv should be name, cost, base, team, country, type, score'
    }

    if request.method == "GET":
        return render(request, template, prompt)

    file = request.FILES['file']

    if not file.name.endswith('.csv'):
        messages.error(request, "This file is not a .csv file")
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
def player_ownership_upload(request):
    template = "ipl2019/upload_csv.html"
    prompt = {
        'order': 'Order of player ownership csv should be player, number, member, price'
    }

    if request.method == "GET":
        return render(request, template, prompt)

    file = request.FILES['file']

    if not file.name.endswith('.csv'):
        messages.error(request, "This file is not a .csv file")
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
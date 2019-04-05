import csv

from django.shortcuts import render
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Member, Player
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
            user1 = User.objects.get(username=column[0])
            member = Member.objects.get(user=user1.id)
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
        'order': 'Order of member csv should be name, cost, base, team, country, type, score'
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
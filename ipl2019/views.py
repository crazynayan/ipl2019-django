import csv, io

from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Member



class MemberView(LoginRequiredMixin, View):
    def get(self, request):
        member_list = Member.objects.all()
        context = {
            'member_list': member_list
        }
        return render(request, 'ipl2019/member_list.html', context)


@permission_required('ipl2019.auctioneer')
def member_upload(request):
    template = "ipl2019/upload_csv.html"
    prompt = {
        'order': 'Order of member csv should be user, name, balance, points'
    }
    if request.method == "GET":
        return render(request, template, prompt)

    csv_file = request.FILES['file']

    data_set = csv_file.read().decode('utf-8')
    io_string = io.StringIO(data_set)
    next(io_string)

    for column in csv.reader(io_string, delimiter=',', quotechar="|"):
        try:
            user1 = User.objects.get(username=column[0])
            member = Member.objects.get(user=user1.id)
            member.name = column[1]
            member.balance = column[2]
            member.points = column[3]
            member.save()
        except ObjectDoesNotExist:
            pass
        # if User.objects.filter(username=column[0]).exists():
        #     userid = User.objects.get(username=column[0]).id
        #     if Member.objects.filter(user=userid).exists():
        #         member =
        #     member = Member.objects.get
        #     _, created = Member.objects.update_or_create(
        #         defaults = {
        #             'name'      : column[1],
        #             'balance'   : column[2],
        #             'points'    : column[3],
        #             },
        #         user=userid
        #     )

    return HttpResponseRedirect(reverse('member_list'))

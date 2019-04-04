from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin#, PermissionRequiredMixin
from .models import Member


class MemberView(LoginRequiredMixin, View):
    def get(self, request):
        member_list = Member.objects.all()
        context = {
            'member_list': member_list
        }
        return render(request, 'ipl2019/member_list.html', context)
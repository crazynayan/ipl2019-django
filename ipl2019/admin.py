from django.contrib import admin
from .models import Member
# Register your models here.
#admin.site.register(Member)


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'points', 'balance', 'user')

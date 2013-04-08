from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from home.models import Blog
from home.models import Hacker

class HackerInline(admin.StackedInline):
    model = Hacker
    can_delete = False

class UserAdmin(UserAdmin):
    inlines = (HackerInline, )

class HomeAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Hacker Schoolers',                  {'fields': ['email', 'first_name', 'last_name']}),
        ('Blogs',                             {'fields': ['user', 'url']}),
    ]

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
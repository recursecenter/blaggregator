from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from home.models import Blog, Hacker, Post

class HackerInline(admin.StackedInline):
    model = Hacker
    can_delete = False

class BlogInline(admin.StackedInline):
    model = Blog
    can_delete = False


class UserAdmin(UserAdmin):
    inlines = (HackerInline, BlogInline)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Post)

from home.models import User, Blog
from django.contrib import admin

class HomeAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Hacker Schoolers',                  {'fields': ['email', 'first_name', 'last_name']}),
        ('Blogs',                             {'fields': ['user', 'url']}),
    ]

admin.site.register(User)
admin.site.register(Blog)
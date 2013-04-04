from home.models import User
from django.contrib import admin

class HomeAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,                  {'fields': ['email', 'first_name', 'last_name']}),
    ]

admin.site.register(User)
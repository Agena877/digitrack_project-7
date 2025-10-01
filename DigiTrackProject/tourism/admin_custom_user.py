from django.contrib import admin
from .models import CustomUser
from django.contrib.auth.admin import UserAdmin

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'name', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password', 'name')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'name', 'password1', 'password2', 'is_staff', 'is_active')
        }),
    )
    search_fields = ('username', 'name')
    ordering = ('username',)

admin.site.register(CustomUser, CustomUserAdmin)

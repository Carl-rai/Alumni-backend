from django.contrib import admin
from .models import CustomUser

class CustomUserModelAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'role', 'alumni_id')
    search_fields = ('last_name', 'email', 'alumni_id')
    list_filter = ('role', 'is_active', 'status')
    list_per_page = 10
    
    fieldsets = (
        ('Personal Info', {
            'fields': ('email', 'first_name', 'middle_name', 'last_name', 'gender', 'age', 'profile_image')
        }),
        ('User (Alumni) Info', {
            'fields': ('alumni_id', 'course', 'year_graduate')
        }),
        ('Staff/Admin Info', {
            'fields': ('position',)
        }),
        ('Permissions', {
            'fields': ('role', 'status', 'is_active', 'is_staff', 'is_superuser', 'password')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            if 'password' in form.changed_data:
                obj.set_password(obj.password)
        else:
            if 'password' in form.changed_data:
                obj.set_password(obj.password)
        
        if obj.role == 'admin':
            obj.is_staff = True
            obj.is_superuser = True
        elif obj.role == 'staff':
            obj.is_staff = True
            obj.is_superuser = False
        else:
            obj.is_staff = False
            obj.is_superuser = False
            
        super().save_model(request, obj, form, change)

admin.site.register(CustomUser, CustomUserModelAdmin)
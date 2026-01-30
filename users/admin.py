from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from rangefilter.filters import DateRangeFilter, DateTimeRangeFilter
from dtb.settings import DEBUG

from users.models import Location, GroupRoles, User, Options, Updates, UsersOptions
from users.forms import BroadcastForm

from users.tasks import broadcast_message
from tgbot.handlers.broadcast_message.utils import send_one_message


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        'user_id', 'username', 'first_name', 'last_name', 
        'roles', "is_blocked_bot",'updated_at','created_at'
    ]
    list_filter = ["is_blocked_bot", ]
    search_fields = ('username', 'user_id')
    filter_horizontal = ('groups', )  # Добавляет удобный интерфейс выбора групп
    actions = ['broadcast']

    def broadcast(self, request, queryset):
        """ Select users via check mark in django-admin panel, then select "Broadcast" to send message"""
        user_ids = queryset.values_list('user_id', flat=True).distinct().iterator()
        if 'apply' in request.POST:
            broadcast_message_text = request.POST["broadcast_text"]

            if DEBUG:  # for test / debug purposes - run in same thread
                for user_id in user_ids:
                    send_one_message(
                        user_id=user_id,
                        text=broadcast_message_text,
                    )
                self.message_user(request, f"Just broadcasted to {len(queryset)} users")
            else:
                broadcast_message.delay(text=broadcast_message_text, user_ids=list(user_ids))
                self.message_user(request, f"Broadcasting of {len(queryset)} messages has been started")

            return HttpResponseRedirect(request.get_full_path())
        else:
            form = BroadcastForm(initial={'_selected_action': user_ids})
            return render(
                request, "admin/broadcast_message.html", {'form': form, 'title': u'Broadcast message'}
            )

@admin.register(UsersOptions)
class UsersOptionsAdmin(admin.ModelAdmin):
     list_display = ['name','user_id','value', 'description']
     search_fields = ('name','value', 'description')
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_id', 'created_at']

@admin.register(GroupRoles)
class GroupRolesAdmin(admin.ModelAdmin):
    list_display = ['name','roles', 'description', 'created_at']

@admin.register(Options)
class OptionsAdmin(admin.ModelAdmin):
    list_display = ['name','value', 'description']
    search_fields = ('name','value', 'description')

@admin.register(Updates)
class UpdatesAdmin(admin.ModelAdmin):
    list_display = ['update_id','message','created_at','from_id', 'json','chat_id']
    search_fields = ('message', 'json')
    # list_filter = ['created_at']
    list_filter = [
        'created_at',                    # 1. Простой фильтр (по конкретным датам)
        ('created_at', DateRangeFilter), # 2. Фильтр диапазона (от и до)
        ('created_at', DateTimeRangeFilter),
    ]

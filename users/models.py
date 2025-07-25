from __future__ import annotations

from typing import Union, Optional, Tuple

from django.db import models
from django.db.models import QuerySet, Manager
from telegram import Update
from telegram.ext import CallbackContext

from tgbot.handlers.utils.info import extract_user_data_from_update
from utils.models import CreateUpdateTracker, nb, CreateTracker, GetOrNoneManager
from dtb.settings import get_plugins, settings

class AdminUserManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_admin=True)
    
class GroupRoles(CreateTracker):
    name = models.CharField(("Название"), max_length=80, unique=True)
    description = models.TextField(("Описание"), default='',blank=True)
    #roles = models.ForeignKey(Roles, default='',on_delete=models.CASCADE, related_name='group_roles')
    roles = models.CharField(max_length=2000,default=',',help_text="Роли пользователя через запятую", **nb)
    objects = GetOrNoneManager()

    def __str__(self):
        return f"{self.name}, {self.description}"

class User(CreateUpdateTracker):
    user_id = models.PositiveBigIntegerField(primary_key=True)  # telegram_id
    username = models.CharField(max_length=32, **nb)
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256, **nb)
    language_code = models.CharField(max_length=8, help_text="Telegram client's lang", **nb)
    deep_link = models.CharField(max_length=64, **nb)
    is_blocked_bot = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_superadmin = models.BooleanField(default=False)
    roles = models.CharField(max_length=2000,default=',',help_text="Роли пользователя через запятую", **nb)
    #roles = models.ForeignKey(Roles, default='',on_delete=models.CASCADE, related_name='users_with_role')
    groups = models.ManyToManyField(GroupRoles, related_name='users', blank=True) #, on_delete=models.SET_NULL)

    objects = GetOrNoneManager()  # user = User.objects.get_or_none(user_id=<some_id>)
    admins = AdminUserManager()  # User.admins.all()

    def __str__(self):
        return f'@{self.username}' if self.username is not None else f'{self.user_id}'
        # _group = f'({self.groups})' if self.groups else ''
        # return f"user: {self.user}, created at {self.created_at.strftime('(%H:%M, %d %B %Y)')} {_group}"

    @classmethod
    def get_user_and_created(cls, update: Update, context: CallbackContext) -> Tuple[User, bool]:
        """ python-telegram-bot's Update, Context --> User instance """
        data = extract_user_data_from_update(update)
        u, created = cls.objects.update_or_create(user_id=data["user_id"], defaults=data)

        if created:
            # Save deep_link to User model
            if context is not None and context.args is not None and len(context.args) > 0:
                payload = context.args[0]
                if str(payload).strip() != str(data["user_id"]).strip():  # you can't invite yourself
                    u.deep_link = payload
                    u.save()
        if u.roles==None or u.roles==",": # Роли по умолчанию присвоим новому пользователю
            u.roles = settings.get("ROLES_DFLT","NEWS,WEATHER,WIKI,CODE,INET,TASKS")
            u.save()
        return u, created

    @classmethod
    def get_user(cls, update: Update, context: CallbackContext) -> User:
        u, _ = cls.get_user_and_created(update, context)
        return u

    @classmethod
    def get_user_by_username_or_user_id(cls, username_or_user_id: Union[str, int]) -> Optional[User]:
        """ Search user in DB, return User or None if not found """
        username = str(username_or_user_id).replace("@", "").strip().lower()
        if username.isdigit():  # user_id
            return cls.objects.filter(user_id=int(username)).first()
        return cls.objects.filter(username__iexact=username).first()

    def get_all_roles(self):
        """
        Метод возвращает все уникальные роли пользователя, включая собственные и унаследованные от групп.
        :return: Список строк с уникальными ролями
        """
        own_roles = set(self.roles.split(',')) if self.roles else set()
        group_roles = set()
        
        for group in self.groups.all():
            group_roles.update(group.roles.split(','))
            
        all_roles = list((own_roles | group_roles) - {''})
        return sorted(all_roles)

    @property
    def invited_users(self) -> QuerySet[User]:
        return User.objects.filter(deep_link=str(self.user_id), created_at__gt=self.created_at)

    @property
    def tg_str(self) -> str:
        if self.username:
            return f'@{self.username}'
        return f"{self.first_name} {self.last_name}" if self.last_name else f"{self.first_name}"

class Location(CreateTracker):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()
    objects = GetOrNoneManager()
    def __str__(self):
        return f"user: {self.user}, created at {self.created_at.strftime('(%H:%M, %d %B %Y)')}"

class UsersOptions(CreateTracker):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=132,unique=True, **nb,help_text="Имя параметра")
    description = models.TextField(("Описание"), default='',blank=True,help_text="Описание параметра")
    category = models.CharField(max_length=256,default='dflt',help_text="Категория параметра")
    type = models.CharField(max_length=256, **nb,default='str',help_text="Тип параметра")
    value = models.TextField(default='',help_text="Значение параметра")
    enabled = models.BooleanField(default=True,help_text="Включено")
    objects = GetOrNoneManager()
    def __str__(self):
        return f"user: {self.user}, created at {self.created_at.strftime('(%H:%M, %d %B %Y)')}"

class Options(CreateTracker):
    name = models.CharField(max_length=132,unique=True, **nb,help_text="Имя параметра")
    description = models.TextField(("Описание"), default='',blank=True,help_text="Описание параметра")
    category = models.CharField(max_length=256,default='dflt',help_text="Категория параметра")
    type = models.CharField(max_length=256, **nb,default='str',help_text="Тип параметра")
    value = models.TextField(default='',help_text="Значение параметра")
    roles = models.CharField(max_length=2000,default=',',help_text="Роли через запятую, которые можно использовать с параметром", **nb)
    enabled = models.BooleanField(default=True,help_text="Включено")
    objects = GetOrNoneManager()
    def __str__(self):
        return f" {self.name}, {self.category}"
    
    @classmethod
    def get_by_name_and_category(cls, name, category=None):
        """Получает объект по имени и дополнительной фильтрации по категории."""
        queryset = cls.objects.filter(name=name)
        if category:
            queryset = queryset.filter(category=category)
        return queryset.first()

class Updates(CreateTracker):
    update_id = models.PositiveBigIntegerField(primary_key=True)
    message = models.TextField(default='',blank=True, null=True)
    from_id = models.BigIntegerField(**nb)
    chat_id = models.BigIntegerField(default=0,null=True, blank=True)
    json = models.TextField(default='',null=True)
    objects = GetOrNoneManager()
    def __str__(self):
        return f" {self.update_id}, {self.from_id}"
    
    @classmethod
    def save_from_update(cls, update: Update) -> Updates:
        """Метод сохраняет обновление в базу данных."""
        try:
            # Пытаемся получить существующее обновление по update_id
            existing_update = cls.objects.get(update_id=update.update_id)
            return existing_update  # Вернем существующий экземпляр
        except cls.DoesNotExist:
            pass  # Запись отсутствует, продолжаем создание новой

        # Устанавливаем text сообщения, если оно доступно
        message_text = getattr(update.message, 'text', '')
        if not message_text:
            message_text = '(Нет текста)'  # Или любое другое подходящее значение по умолчанию

        new_update = cls(
            update_id=update.update_id,
            message=message_text,
            from_id=getattr(getattr(update.message, 'from_user', None), 'id', None),
            chat_id=getattr(update.message, 'chat_id', None),
            json=str(update.to_dict())
        )
        new_update.save()  # Создаем новый экземпляр в БД
        return new_update
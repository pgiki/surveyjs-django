from dotty_dict import dotty
from ast import operator
from functools import reduce
import re
import os

# for build_or_condtion
from django.db.models import Q
import operator
from django.contrib.contenttypes.models import ContentType
from guardian.models import Group
from functools import reduce
import operator
import phonenumbers
from django.conf import settings

# permissions
from guardian.core import ObjectPermissionChecker
from django.contrib.auth import get_user_model
from guardian.shortcuts import (
    assign_perm,
    get_users_with_perms,
    get_groups_with_perms,
    remove_perm,
    get_objects_for_user,  
)
import phonenumbers
from notifications.signals import notify
import requests
import json
from django.utils import timezone

# django models
User = get_user_model()

def  emit_event(event_name, data, room=None):
    pass

def get_bot_user():
    return User.objects.filter(is_superuser=True).first()


def get_system_user():
    return User.objects.filter(is_superuser=True).first()

def inherit_permissions(
    from_obj, to_object, perm_transformer=None, permissions=None, remove=False
):
    """
    inherit permissions from one object to another object
    if permissions is dictionary, only those permissions will be validated
    """
    from_obj_users = get_users_with_perms(from_obj, attach_perms=True)
    from_obj_groups = get_groups_with_perms(from_obj, attach_perms=True)
    from_obj_users_groups = {**from_obj_users, **from_obj_groups}
    # inherit user/group permissions to
    for user_group, perms in from_obj_users_groups.items():
        for perm in perms:
            if permissions and not perm in permissions.keys():
                continue

            mapped_permissions = (
                perm_transformer(perm) if perm_transformer else permissions.get(perm)
            )
            if mapped_permissions:
                for mapped_permission in mapped_permissions:
                    if remove:
                        remove_perm(
                            mapped_permission,
                            user_group,
                            to_object,
                        )
                    else:
                        assign_perm(
                            mapped_permission,
                            user_group,
                            to_object,
                        )


def get_permissions(obj=None, user=None):
    try:
        if not hasattr(user, '_meta'):
            return []
        checker = ObjectPermissionChecker(user)  # we can pass user or group
        return checker.get_perms(obj)
    except Exception as e:
        print("Error get permissions ", e, obj)
        return []


def get_content_type(obj=None, model=None):
    return ContentType.objects.get_for_model(obj or model)


def assign_permissions_to_object(
    obj=None,
    user_or_group=None,
    permissions=["add", "change", "delete", "view"],
    model_name=None,
):
    """
    Assign permission to every newly created item
    give all permissions to the user who created it
    """
    for perm in permissions:
        p = perm
        # if simple permissions then add model_name to it
        if len(p.split("_")) == 1:
            if not model_name:
                content_type = get_content_type(obj)
                model_name = content_type.model
            p = f"{perm}_{model_name}"
        assign_perm(p, user_or_group, obj)


def build_or_condition(fields, search=""):
    query = Q()
    if not search:
        return query

    my_dict = {}
    terms = [search]  # .split() split terms into words
    for term in terms:
        for field in fields:
            if field:
                my_dict[f"{field}__icontains"] = term

    keys = [(key, my_dict[key]) for key in my_dict]
    q_list = [Q(x) for x in keys]
    try:
        query = reduce(operator.or_, q_list)
    except Exception as e:  # if empty string and sometimes for no reasons fails
        print("Error building query", search, e)
        pass
    return query


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[-1].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def get_object(obj, path, default=None):
    """
    fails for nested lists so work on it love
    """
    dot = dotty(obj)
    try:
        return dot[path]
    except:
        return default


def create_object(obj={}, path=None, value=None):
    """
    creates a json object by specifying path using dot notation
    @obj eg {}
    @path eg a.b
    @value eg "c"
    return {"a":{"b":"c"}}
    """
    dot = dotty(obj)
    dot[path] = value
    return dict(dot)


def remove_keys(obj, keys):
    """
    convert dictionary to dot and then
    """
    dot = dotty(obj)
    for key in keys:
        try:
            del dot[key]
        except Exception as e:
            # print("Error deleting key")
            pass
    return dict(dot)


def get_class_attr(obj, path, default=None):
    """
    Easily access attr from class
    @obj = Class
    @path = [Class].y.z
    """
    if not obj:
        return default if obj is None else obj

    splits = path.split(".")
    for s in splits:
        obj = getattr(obj, s, default)
        if not obj:
            break
    return default if obj is None else obj


def replace_variables(s="", variables=dict()):
    """
    if any of the variables is None, return None for entire s
    """
    if s and hasattr(s, "__call__"):
        # replace the return function result just in case
        return replace_variables(s(variables), variables)

    if not s or type(s) is not str:
        return s

    variable_keys = re.compile(
        r"\{(\w+\.*\w*\.*\w*\.*\w*\w+\.*\w*\.*\w*\.*\w*)\}"
    ).findall(s)

    for variable_key in variable_keys:
        value = get_object(variables, variable_key, None)
        if value is None:
            return None
        s = s.replace("{" + variable_key + "}", str(value))

    try:
        s = eval(s)
    except:
        pass
    return s


def handle_group_permissions(instance, group_permissions=[],  action="add"):
    """Get all permissions from yml schema document and then assign to the user accordingly
    Args:
        instance (_type_): The object to assign permissions to
        action (str, optional): add|remove. Defaults to "add".
        group_permissions (list, optional) the list of permissions to be assigned. If not given defaults to the schema file
    Returns:
        _type_: _description_
    """
    if not group_permissions:
        obj_content_type = ContentType.objects.get_for_model(instance)
        model_path = f'{obj_content_type.app_label}.{instance.__class__.__name__}'
        group_permissions = settings.PERMISSIONS_SCHEMA.get(model_path, [])

    def get_group_name(item, category=None):
        if type(item) is str:  # custom group name
            return f"{item} {category}" if category else item
        return (item.get_group_name(category) if
                (item and hasattr(item, "get_group_name")) else None)

    def get_object_from_obj(obj, path, default=None):
        if path.startswith("group:"):
            return path.replace("group:", "").strip()
        if 'eval:' in path:
            evaluated = eval(path.replace('eval:', ''))
            return evaluated
        else:
            return get_class_attr(obj, path, default)
        
    def assign_permissions_to_group(group_name, permissions=[]):
        group, group_created = Group.objects.get_or_create(name=group_name)
        if group_created:
            guessed_username = group_name.split()[0]
            guessed_user = User.objects.filter(
                username=guessed_username).first()
            if guessed_user:
                # give view only permission to user who is likely the owner of this group
                assign_permissions_to_object(
                    obj=group,
                    user_or_group=guessed_user,
                    permissions=["view_group"],
                )
        if action == "add":
            assign_permissions_to_object(
                obj=instance,
                user_or_group=group,
                permissions=permissions,
            )
        elif action == "remove":
            for p in permissions:
                remove_perm(p, group, instance)

    for group_permission in group_permissions:
        category = ''
        if len(group_permission)>2:
            category = group_permission[2]
        if group_permission:
            permissions=group_permission[1]
            group_name_parts = []
            _group_name = group_permission[0]
            for path in _group_name.split("+"):
                item = get_object_from_obj(instance, path)
                if not item:
                    continue
                # this should be an iterable returned from the eval
                if not type(item) is str:
                    for _item in item:
                        group_name = get_group_name(
                            _item, category=category)
                        if group_name:
                            assign_permissions_to_group(group_name, permissions)
                else:
                    group_name_parts.append(item)
                    group_name = " | ".join(
                        list(
                            filter(
                                lambda x: not x is None,
                                [
                                    get_group_name(item, category=category)
                                    for item in group_name_parts
                                ],
                            ))).strip()
                    if group_name:
                        assign_permissions_to_group(group_name, permissions)

    return True

def to_python_value(value):
    if value == "false":
        return False
    elif value == "true":
        return True
    elif value and value.isdigit():
        return eval(value)
    return value


def generate_query(field=str, terms=list, qtype="or", connector="__iexact"):
    query = Q()
    if not terms:
        return query

    # for integer fields make sure there is not connector
    if field.endswith(
        (
            "id",
            "pk",
        )
    ):
        connector = ""

    keys = [(f"{field}{connector}", to_python_value(term)) for term in terms]
    q_list = [Q(x) for x in keys]
    try:
        if qtype == "and":
            query = reduce(operator.and_, q_list)
        else:
            query = reduce(operator.or_, q_list)
    except Exception as e:  # if empty string and sometimes for no reasons fails
        print("Error getting query", e)
        pass
    # print(query)
    return query


def format_phone(n, country="TZ"):
    """Return original string if not formatted"""
    if n and len(n) < 8:
        return (False, n)

    try:
        z = phonenumbers.parse(n, country)
        is_valid = phonenumbers.is_valid_number(z)
        return (
            is_valid,
            phonenumbers.format_number(z, phonenumbers.PhoneNumberFormat.E164),
        )
    except Exception as e:
        # print("Error format_phone", e, n)
        return (False, n)

# chats helpers
def emit_unread_notifications(user):
    qs_count = (
        get_objects_for_user(user, "notifications.view_notification")
        .filter(unread=True)
        .count()
    )
    emit_event("notifications_count", qs_count, room=f"user_{user.id}")


def sendsms(phone=None, message=None, url=None, user=None, event=None):
    if not event:
        if user and not phone:
            # get phone from user object
            phone = user.username
        if not phone:
            return {"error": "`phone` or `user` is required"}

    SMSBOMBA_URL = url or os.getenv("SMSBOMBA_URL")
    event = event or {
        "events": [
            {
                "event": "send",
                "action": "amqp",
                "created_at": str(timezone.now()),
                "messages": [{"message": message, "to": phone}],
            }
        ]
    }
    headers = {"Content-type": "application/json", "Accept": "application/json"}
    try:
        res = requests.post(SMSBOMBA_URL, data=json.dumps(event), headers=headers)
        return json.dumps(res.json())
    except Exception as e:
        print("Error sending message ", e)
        return {"error": str(e)}


def notify_users(
    users=[],
    title=None,
    body=None,
    data=dict(),
    sender=None,
    action_object=None,
    sms_url=None,
    public=False,
    level="info",
    target=None,
    save=True,
    channels=[],  # how would like this message sent [sms, email]
    **kwargs,
):
    """
    channels=[],  # how would like this message sent [sms, email]
    actor: An object of any type. (Required) Note: Use sender instead of actor if you intend to use keyword arguments
    recipient: A Group or a User QuerySet or a list of User. (Required)
    verb: An string. (Required)
    action_object: An object of any type. (Optional)
    target: An object of any type. (Optional)
    level: One of Notification.LEVELS ('success', 'info', 'warning', 'error') (default=info). (Optional)
    description: An string. (Optional)
    public: An boolean (default=True). (Optional)
    timestamp: An tzinfo (default=timezone.now()). (Optional)
    """
    users_qs = User.objects.filter(id__in=users) if type(users) is list else users
    sender = sender or get_bot_user()
    if "sms" in channels and sms_url:
        for user in users_qs:
            sendsms(user=user, message=body, url=sms_url)

    if save:
        notify.send(
            sender=sender,
            recipient=users_qs,
            verb=title,
            description=body,
            public=public,
            action_object=action_object,
            target=target,
            level=level,
            channels=channels,
            **kwargs,
        )

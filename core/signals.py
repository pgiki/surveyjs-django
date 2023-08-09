from . import models
from django.conf import settings
from django.db.models import Q
from django.db.models.signals import post_save, pre_delete, m2m_changed
from django.dispatch import receiver
from guardian.shortcuts import assign_perm

# from guardian.shortcuts import get_objects_for_user
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from .utils import helpers

User = get_user_model()

def add_group_permissions(group):
    """
    This is a hacky way to automatically add users to groups
    """
    usernames = [name.strip() for name in group.name.split("|")]
    if len(usernames) > 2:
        users = User.objects.filter(username__in=usernames)
        for action in ["change", "delete", "view", "add"]:
            for user in users:
                assign_perm(f"{action}_group", user, group)


@receiver(post_save, sender=Group)
def group_post_save(sender, **kwargs):
    """
    assign access permissions to user to their own group if created
    """
    group, created = kwargs["instance"], kwargs["created"]
    if created:
        add_group_permissions(group)


def on_user_username_update_or_create(user):
    """
    assign permission to manage their own profiles
    Also add permission for the user to view and manage their own profiles
    Add newly created user to everyone group
    """
    username = user.username
    everyone = Group.objects.get_or_create(name=settings.getattr('EVERYONE_GROUP_NAME', 'everyone'))[0]
    # create group so they can easily share with other users
    self_group = Group.objects.get_or_create(name=username)[0]
    user.groups.add(everyone)
    user.groups.add(self_group)
    # add permission so they can see themselves and their profile
    assign_perm(f"view_group", user, self_group)
    # give them more control over their groups
    for perm in ["add", "change", "view"]:
        assign_perm(f"{perm}_user", user, user)

@receiver(post_save, sender=User)
def user_post_save(sender, **kwargs):
    """
    assign permission to manage their own profiles
    Also add permission for the user to view and manage their own profiles
    Add newly created user to everyone group
    """
    user, created = kwargs["instance"], kwargs["created"]
    username = user.username
    if created and username != settings.getattr('ANONYMOUS_USER_NAME', 'nobody'):
        # create profile automatically too
        on_user_username_update_or_create(user)
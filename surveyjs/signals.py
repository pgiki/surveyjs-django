
from . import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from core.utils import helpers
User = get_user_model()


@receiver(post_save, sender=models.Survey)
def Survey_post_save(sender, **kwargs):
    """ """
    item, created = kwargs["instance"], kwargs["created"]
    if created:
        helpers.handle_group_permissions(item)

@receiver(post_save, sender=models.Result)
def Result_post_save(sender, **kwargs):
    """ """
    item, created = kwargs["instance"], kwargs["created"]
    if created:
        helpers.handle_group_permissions(item)
        helpers.notify_users(
            users=User.objects.filter(is_superuser=True),
            title="New Submission",
            data={"next_screen": "Dashboard"},
            body="Submission with id %s created at %s" % (item.id, item.created),
        )

@receiver(post_save, sender=models.Attachment)
def Attachment_post_save(sender, **kwargs):
    """ """
    item, created = kwargs["instance"], kwargs["created"]
    if created:
        helpers.handle_group_permissions(item)

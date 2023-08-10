import base64
from django.conf import settings
from django.core.files.base import ContentFile
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from rest_framework import serializers, status, permissions

# from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from . import helpers

# for extra actions
from rest_framework import status
from rest_framework.decorators import action
from django.db.models import Q
from guardian.shortcuts import (
    assign_perm,
    remove_perm,
    get_users_with_perms,
    # get_objects_for_user,
    get_groups_with_perms,
)
from guardian.models import Group
from rest_framework_guardian import filters

from django_restql.mixins import QueryArgumentsMixin
from django_restql.parser import QueryParser
from django.contrib.auth import get_user_model

User = get_user_model()
# for custom create
from rest_framework.utils import model_meta
from rest_framework.serializers import traceback
from sorl.thumbnail import get_thumbnail


class PermissionsMixin:
    def get_permissions(self, obj, parsed_query=None):
        try:
            if self.context and self.context.get("request", None):
                user = self.context["request"].user
                return helpers.get_permissions(obj=obj, user=user)
            return []
        except:
            return []

    def original_create(self, validated_data):
        """
        We have a bit of extra checking around this in order to provide
        descriptive messages when something goes wrong, but this method is
        essentially just:
            return ExampleModel.objects.create(**validated_data)
        If there are many to many fields present on the instance then they
        cannot be set until the model is instantiated, in which case the
        implementation is like so:
            example_relationship = validated_data.pop('example_relationship')
            instance = ExampleModel.objects.create(**validated_data)
            instance.example_relationship = example_relationship
            return instance
        The default implementation also does not handle nested relationships.
        If you want to support writable nested relationships you'll need
        to write an explicit `.create()` method.
        """
        ModelClass = self.Meta.model
        info = model_meta.get_field_info(ModelClass)
        many_to_many = {}
        for field_name, relation_info in info.relations.items():
            if relation_info.to_many and (field_name in validated_data):
                many_to_many[field_name] = []
                many_to_many_values = validated_data.pop(field_name)
                for action in ["add", "create"]:
                    many_to_many[field_name] += many_to_many_values.get(action, [])

        constrained_data = dict()
        for constraint in self.Meta.model._meta.constraints:
            for field in constraint.fields:
                if field in validated_data:
                    constrained_data[field] = validated_data.pop(field)
        try:
            if constrained_data:
                instance, created = ModelClass._default_manager.update_or_create(
                    **constrained_data, defaults=validated_data
                )
            else:
                instance = ModelClass._default_manager.create(**validated_data)
        except TypeError:
            tb = traceback.format_exc()
            msg = (
                "Got a `TypeError` when calling `%s.%s.create()`. "
                "This may be because you have a writable field on the "
                "serializer class that is not a valid argument to "
                "`%s.%s.create()`. You may need to make the field "
                "read-only, or override the %s.create() method to handle "
                "this correctly.\nOriginal exception was:\n %s"
                % (
                    ModelClass.__name__,
                    ModelClass._default_manager.name,
                    ModelClass.__name__,
                    ModelClass._default_manager.name,
                    self.__class__.__name__,
                    tb,
                )
            )
            raise TypeError(msg)

        # Save many-to-many relationships after the instance is created.
        if many_to_many:
            for field_name, value in many_to_many.items():
                field = getattr(instance, field_name)
                field.set(value)
        return instance


class ObjectPermissions(permissions.DjangoObjectPermissions):
    """
    Similar to `DjangoObjectPermissions`, but adding 'view' permissions.
    """

    perms_map = {
        "GET": ["%(app_label)s.view_%(model_name)s"],
        "OPTIONS": ["%(app_label)s.view_%(model_name)s"],
        "HEAD": ["%(app_label)s.view_%(model_name)s"],
        "POST": ["%(app_label)s.add_%(model_name)s"],
        "PUT": ["%(app_label)s.change_%(model_name)s"],
        "PATCH": ["%(app_label)s.change_%(model_name)s"],
        "DELETE": ["%(app_label)s.delete_%(model_name)s"],
    }


class AvatarMixin(serializers.ModelSerializer):
    """
    get an avatar, with default dimensions or specific ones
    """

    avatar = serializers.SerializerMethodField()

    def get_avatar(self, obj, query=None):
        request = self.context["request"]
        photo = None
        if hasattr(self, "get__avatar"):
            photo = self.get__avatar(obj)
        else:
            photo = obj.avatar
        size = request.GET.get("avatar[size]")
        if photo:
            photo_url = (
                get_thumbnail(photo, size, crop="center", quality=99).url
                if size
                else photo.url
            )
            return request.build_absolute_uri(photo_url)
        else:
            return None


class MixinViewSet(QueryArgumentsMixin):
    """
    A base class for all viewset
    """

    filterset_fields = ["id"]
    filter_by_user = False
    errors = []  # validation errors
    permission_classes = [ObjectPermissions]
    filter_backends = [filters.ObjectPermissionsFilter]

    def check_has_perm(self, user_or_group=None, obj=None, perm=None):
        # checker = ObjectPermissionChecker(user_or_group)  # we can pass user or group
        return user_or_group.has_perm(perm)

    def get_user_or_group(self):
        """
        a quick way to get user or group to be assigne permission too,
        can also receive list of user/group_id
        """
        from core.serializers import GroupSerializer

        user__id = self.request.GET.get("user__id", self.request.data.get("user__id"))
        group__id = self.request.GET.get(
            "group__id", self.request.data.get("group__id")
        )
        user_or_group = []
        if user__id:
            user_or_group = user_or_group + [
                item for item in User.objects.filter(id__in=user__id.split(","))
            ]
        if group__id:
            user_or_group = user_or_group + [
                item
                for item in GroupSerializer.Meta.model.objects.filter(
                    id__in=group__id.split(",")
                )
            ]

        if not (user__id or group__id):
            user_or_group = user_or_group + [
                item for item in User.objects.filter(id=self.request.user.id)
            ]
        return user_or_group

    @action(
        detail=True,
        methods=["GET", "POST"],
        name="Check if logged in user has permission",
    )
    def has_perm(self, request, *args, **kwargs):
        """
        Get @permission__codename and @user__id/group__id eg {"permission__codename":"add_branch", "user__id":12} \n
        if  @user__id is missing in the request, the given permission is assigned to the user sending the request\n
        @permission__codename can also be a list of permissions to be checked eg  {"permission__codename":"add_branch,delete_branch", "user__id":12}
        """
        obj = self.get_object()
        user = self.get_user_or_group()
        # to check only check for the first item
        perm_name = request.GET.get(
            "permission__codename", request.data.get("permission__codename")
        )
        has_perm = []
        if user and perm_name:
            for _user in user:
                perm = dict()
                for p in perm_name.split(","):
                    p = p.strip()
                    has_permission = self.check_has_perm(_user, obj=obj, perm=p)
                    perm.update({p: has_permission})
                has_perm.append(perm)

        return Response(
            {
                "has_permission": has_perm,
                "permission__codename": perm_name,
            }
        )

    @action(
        detail=True,
        methods=["POST"],
        name="Assign a permission object",
    )
    def assign_perm(self, request, *args, **kwargs):
        """
        Example POST: {
                add:{
                    users:[1,2,3],
                    groups:[3,5],
                    permissions:["view_item"]
                },
                remove:{
                    users:[1,2,3],
                    groups:[3,4],
                    permissions:["view_item"],
                }
            }
        Note: Users cannot remove themselves from an item because that means loosing access
        """
        obj = self.get_object()
        data = request.data.copy()
        logged_user = request.user

        add_users = helpers.get_object(data, "add.users")
        remove_users = helpers.get_object(data, "remove.users")

        add_groups = helpers.get_object(data, "add.groups")
        remove_groups = helpers.get_object(data, "remove.groups")

        add_permissions = helpers.get_object(data, "add.permissions")
        remove_permissions = helpers.get_object(data, "remove.permissions")
        errors = []

        def _add_permissions(users_or_groups):
            try:
                for p in add_permissions:
                    assign_perm(p, users_or_groups, obj)
            except Exception as e:
                errors.append(str(e))

        def _remove_permissions(users_or_groups):
            try:
                for p in remove_permissions:
                    for user_or_group in users_or_groups:
                        remove_perm(p, user_or_group, obj)
            except Exception as e:
                errors.append(str(e))

        if add_users:
            # add users to this group
            items = User.objects.filter(id__in=add_users)
            _add_permissions(items)

        if remove_users:
            # add users to this group
            items = User.objects.filter(id__in=remove_users).exclude(
                username=logged_user.username
            )
            _remove_permissions(items)

        if add_groups:
            # add users to this group
            items = Group.objects.filter(id__in=add_groups)
            _add_permissions(items)

        if remove_groups:
            items = Group.objects.filter(id__in=remove_groups).exclude(
                name=logged_user.username
            )
            _remove_permissions(items)
        return Response({"success": True, "errors": errors})

    @action(
        detail=False,
        methods=["POST", "GET"],
        name="Assign geneal permissions to a user or logged user",
    )
    def assign_general_perm(self, request, *args, **kwargs):
        """
        POST,GET @permission__codename and @user__id/group__id eg {"permission__codename":"add_branch", "user__id":12} \n
        if  @user__id is missing in the request, the given permission is assigned to the user sending the request\n
        @permission__codename can also be a list of permissions to be checked eg  {"permission__codename":"add_branch,delete_branch", "user__id":12}
        """
        obj = None
        user = self.get_user_or_group()
        perm_name = request.GET.get(
            "permission__codename", request.data.get("permission__codename")
        )
        has_perm = []
        if perm_name and user:
            for u in user:
                perm = dict()
                for p in perm_name.split(","):
                    p = p.strip()
                    assign_perm(p, u, obj)
                    perm.update({p: True})
                has_perm.append(perm)

        return Response(
            {
                "has_permission": has_perm,
                "permission__codename": perm_name,
            }
        )

    @action(
        detail=True,
        methods=["POST", "GET"],
        name="Remove object specific permission to a user",
    )
    def remove_perm(self, request, pk=None, *args, **kwargs):
        """
        Remove user or group permission on an object
        POST,GET @permission__codename and @user__id/@group__id eg {"permission__codename":"add_branch", "user__id":12} \n
        if  @user__id is missing in the request, the given permission is assigned to the user sending the request\n
        @permission__codename can also be a list of permissions to be checked eg  {"permission__codename":"add_branch,delete_branch", "group__id":12}
        """
        obj = self.get_object()
        user = self.get_user_or_group()
        perm_name = request.GET.get(
            "permission__codename", request.data.get("permission__codename")
        )
        has_perm = []
        if perm_name and user:
            for _user in user:
                perm = dict()
                for p in perm_name.split(","):
                    p = p.strip()
                    remove_perm(p, _user, obj)
                    # TODO: check to verify that permission is actually removed
                    perm.update({p: False})
                has_perm.append(perm)

        return Response(
            {
                "has_permission": has_perm,
                "permission__codename": perm_name,
            }
        )

    @action(
        detail=False,
        methods=["POST", "GET"],
        name="Remove general permissions to a user",
    )
    def remove_general_perm(self, request, *args, **kwargs):
        """
        Remove user permission on an object
        POST,GET @permission__codename and @user__id/group__id eg {"permission__codename":"add_branch", "user__id":12} \n
        if  @user__id is missing in the request, the given permission is assigned to the user sending the request\n
        @permission__codename can also be a list of permissions to be checked eg  {"permission__codename":"add_branch,delete_branch", "user__id":12}
        """
        obj = None
        user = self.get_user_or_group()
        perm_name = request.GET.get(
            "permission__codename", request.data.get("permission__codename")
        )
        has_perm = []
        if perm_name and user:
            for _user in user:
                perm = dict()
                for p in perm_name.split(","):
                    p = p.strip()
                    remove_perm(p, _user, obj)
                    # TODO: check to verify that permission is actually removed
                    perm.update({p: False})
                has_perm.append(perm)

        return Response(
            {
                "has_permission": has_perm,
                "permission__codename": perm_name,
            }
        )

    @action(detail=True, methods=["POST", "GET"], name="Get all users with access")
    def permitted_users(self, request, *args, **kwargs):
        """
        Returns queryset of all ``User`` and ``Group`` objects with *any* object permissions for
        the given ``obj``. \n
        Parse ``user_query`` and ``group_query`` if interested to parse the response data for user and group respectively

        """
        # imported here instead of top tp prevent cyclic dependences
        from core.serializers import GroupSerializer, UserSerializer

        # logged_user = request.user
        with_superusers = request.GET.get("with_superusers", "0")
        with_group_users = request.GET.get("with_group_users", "0")
        with_superusers = False if with_superusers in ["0", "false", "False"] else True
        with_group_users = (
            False if with_group_users in ["0", "false", "False"] else True
        )

        obj = self.get_object()
        is_group = isinstance(obj, Group)
        users = get_users_with_perms(
            obj,
            attach_perms=True,
            with_group_users=with_group_users,
            with_superusers=with_superusers,
        )

        groups = get_groups_with_perms(obj, attach_perms=True)
        users_results, groups_results = [], []
        parser = QueryParser()
        user_parsed_query = parser.parse(request.GET.get("user_query", "{*}"))
        group_parsed_query = parser.parse(request.GET.get("group_query", "{*}"))

        for user in users:
            users_results.append(
                {
                    "item": UserSerializer(
                        user,
                        context=self.get_serializer_context(),
                        parsed_query=user_parsed_query,
                    ).data,
                    "permissions": users[user],
                }
            )
        if is_group:
            # get a list of all users with permission
            users = User.objects.filter(groups=obj)
            for u in users:
                users_results.append(
                    {
                        "item": UserSerializer(
                            u,
                            context=self.get_serializer_context(),
                            parsed_query=user_parsed_query,
                        ).data,
                        "permissions": ["view_group"],
                    }
                )

        for group in groups:
            groups_results.append(
                {
                    "item": GroupSerializer(
                        group,
                        context=self.get_serializer_context(),
                        parsed_query=group_parsed_query,
                    ).data,
                    "permissions": groups[group],
                }
            )

        return Response(
            {
                "users": {
                    "count": len(users_results),
                    "results": users_results,
                },
                "groups": {
                    "count": len(groups_results),
                    "results": groups_results,
                },
            }
        )

    def get_host(self):
        request = self.request
        scheme = request.is_secure() and "https" or "http"
        return f"{scheme}://{request.get_host()}"

    def base64_to_file(self, data, name=None):
        _format, _img_str = data.split(";base64,")
        _name, ext = _format.split("/")
        if not name:
            name = _name.split(":")[-1]
            imageBinary = base64.b64decode(_img_str)
            # thumb = get_thumbnail(imageBinary, '350x350', crop='center', quality=50)
            # print("imageSource thumb", thumb)
        uploaded_image = ContentFile(imageBinary, name="{}.{}".format(name, ext))
        return uploaded_image

    def update(self, request, *args, **kwargs):
        data = {key: value for (key, value) in request.data.items()}
        obj = self.get_object()
        user = request.user

        if not self.get_has_perm(f"change", obj=obj, user=user):
            response_status = status.HTTP_406_NOT_ACCEPTABLE
            data = {
                "status_code": response_status,
                "detail": "Sorry, You have no editing powers here babe",
            }
            return Response(data, status=response_status)

        else:
            # print("updating data ", data)
            if hasattr(self, "normalize_data"):
                data = self.normalize_data(data, action="update")

            if hasattr(self, "pre_update"):
                obj = self.pre_update(obj=obj, data=data)

            # pre_update may return NULL if validation failed
            if obj:
                serializer = self.serializer_class(
                    obj, data=data, partial=True, context={"request": request}
                )
                if serializer.is_valid():
                    # print("updating object ", serializer)
                    obj = serializer.save(request=request)
                    self.assign_permissions_to_object(obj=obj, user=request.user)
                    # print("data is saved ", data["avatar"])
                    if hasattr(self, "post_update"):
                        obj = self.post_update(obj=obj, data=data)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(
                    {"errors": self.errors, "success": False},
                    status=status.HTTP_400_BAD_REQUEST,
                )

    def assign_permissions_to_object(self, obj=None, user=None, permissions=[]):
        """
        Assign permission to every newly created item
        give all permissions to the user who created it
        """
        content_type = self.get_content_type(obj)
        model_name = content_type.model
        # include custom permissions too
        permissions = [
            p[0]
            for p in getattr(self.serializer_class.Meta.model._meta, "permissions", [])
        ] + [
            f"{perm}_{model_name}"
            for perm in (permissions or ["add", "change", "delete", "view"])
        ]

        for perm in permissions:
            assign_perm(perm, user, obj)
        permitted_groups = getattr(self, "permitted_groups", [])
        # assign permission to all permitted groups
        for g in permitted_groups:
            group, __ = Group.objects.get_or_create(name=g[0])
            for p in g[1]:
                assign_perm(f"{p}_{model_name}", group, obj)

    def create(self, request, *args, **kwargs):
        # get a deep copy of the data. Useful to save data with file upload
        data = {key: value for (key, value) in request.data.items()}
        user = request.user
        default_currency = helpers.get_class_attr(
            user, "profile.currency", settings.DEFAULT_CURRENCY
        )

        for currency_field in filter(
            lambda f: f.endswith("_currency"), self.serializer_class.Meta.fields
        ):
            if not data.get(currency_field):
                data.update({currency_field: default_currency})

        if hasattr(self, "normalize_data"):
            data = self.normalize_data(data, action="create")

        if (
            "user" in self.serializer_class.Meta.fields
            and not data.get("user")
            and not getattr(self, "user_not_required", False)
        ):
            data.update({"user": user.id})

        serializer = self.serializer_class(data=data, context={"request": request})

        if serializer.is_valid():
            if serializer.Meta.model == User:
                try:
                    obj = serializer.save(request)
                except:
                    obj = serializer.save()
            else:
                obj = serializer.save()

            if hasattr(self, "post_create"):
                obj = self.post_create(obj=serializer.instance, data=data)

            # assign all permissions to the permission who created the object
            self.assign_permissions_to_object(
                obj=obj,
                user=request.user,
                permissions=getattr(self, "user_permissions", []),
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_has_perm(self, perm, obj=None, user=None):
        content_type = self.get_content_type(obj)
        return user.has_perm(f"{perm}_{content_type.model}", obj)

    def destroy(self, request, *args, **kwargs):
        """
        only delete from endpoint items which has user attribute
        if user role is not superuser
        """
        instance = self.get_object()
        user = request.user
        response_status = status.HTTP_200_OK
        data = {"success": False}
        if self.get_has_perm(f"delete", obj=instance, user=user):
            self.perform_destroy(instance)
            data.update({"success": True})

        else:
            response_status = status.HTTP_406_NOT_ACCEPTABLE
            data.update(
                {
                    "status_code": response_status,
                    "detail": "You have no power here babe",
                }
            )
        return Response(data, status=response_status)

    def perform_destroy(self, instance):
        """
        do hard or soft delete
        """
        if hasattr(instance, "is_deleted"):
            instance.is_deleted = True
            if hasattr(instance, "deleted_at"):
                instance.deleted_at = timezone.now()
            instance.save()
        else:
            instance.delete()

    def is_valid_field(self, k):
        k = k.strip()
        parts = k.split("__")
        return (
            "__".join(parts[:-1]) in self.filterset_fields or k in self.filterset_fields
        )

    def get_params_data(self):
        # Filters for list filters
        filters = []
        CAN_ACCEPT_ANY_FIELD = True
        qtype = self.request.GET.get("qtype", "or")
        connector = self.request.GET.get("connector", "__iexact")
        for k, v in self.request.GET.items():
            terms = self.request.GET.getlist(k)
            if k.endswith("[]"):
                k = k.replace("[]", "")
                if self.is_valid_field(k) or CAN_ACCEPT_ANY_FIELD:
                    query = helpers.generate_query(
                        k, terms=terms, qtype=qtype, connector=connector
                    )
                    filters.append(query)
            else:
                if self.is_valid_field(k):
                    if v:
                        data = {k: helpers.to_python_value(v)}
                        query = Q(**data)
                        filters.append(query)
        return filters

    def get_field(self, k, strip=True):
        field = None
        parts = k.split("__") if k else []
        # print("parts", parts, parts[:-1])
        if len(parts) > 1:
            field = "__".join(parts[:-1]) if parts else None
        else:
            field = k
        if not strip:
            return field
        return field and field.strip("-")

    def get_queryset(
        self,
    ):  # TODO: check if The list of topics viewed in the notes part should begin from ascending order to descending order as how written into notepad format.
        queryset = self.queryset
        user = self.request.user
        search = self.request.GET.get("search", "")
        order_by = self.request.GET.get("order_by")
        order_by_field = self.get_field(order_by) if order_by else None
        firstItem = queryset.first()

        distinct = self.request.GET.get("distinct")
        filters = self.get_params_data()
        # filter data only related to the user
        advanced_search = self.request.GET.get("advanced_search")
        if advanced_search:
            for key_value in advanced_search.split(";"):
                try:
                    key, value = key_value.strip().split(":")
                    data = {key: helpers.to_python_value(value)}
                    query = Q(**data)
                    filters.append(query)
                except Exception as e:
                    print("Error getting param, ", e)

        if search:
            or_query = helpers.build_or_condition(self.filterset_fields, search)
            queryset = queryset.filter(or_query)

        for f in filters:
            queryset = queryset.filter(f)

        if self.filter_by_user:
            queryset = queryset.filter(user=user)

        # ordering of results
        # first check if distinct and order_by are valid fields

        # print("The order_by is here", order_by, order_by_field)
        if order_by_field and hasattr(firstItem, order_by_field):
            try:
                if distinct:
                    queryset = queryset.distinct(order_by_field).order_by(order_by)
                else:
                    # print("order_by", order_by)
                    queryset = queryset.order_by(order_by)
            except Exception as error:
                # print("Error order by ", order_by, error)
                pass
        elif distinct:
            try:
                queryset = queryset.order_by(distinct).distinct(distinct)
            except Exception as e:
                pass
        else:
            queryset = queryset.order_by("id")

        if hasattr(self, "extra_queryset"):
            queryset = self.extra_queryset(queryset)
            # if self.kwargs.get("pk") and not order_by:
            #     queryset = queryset.order_by("id").distinct("id")
        return queryset

    def get_content_type(self, obj=None, model=None):
        if model or obj:
            return ContentType.objects.get_for_model(model or obj)
        else:
            return ContentType.objects.get_for_model(self.serializer_class.Meta.model)

    def list(self, request, *args, **kwargs):
        response = super().list(request, args, kwargs)
        user = request.user
        ct = self.get_content_type()
        if type(response.data) is dict:
            response.data.update(
                {
                    "content_type": ct.id,
                    "permissions": {
                        f"can_{p}": self.check_has_perm(
                            user_or_group=user, perm=f"{ct.app_label}.{p}_{ct.model}"
                        )
                        for p in ["change", "view", "delete", "add"]
                    },
                }
            )
        if hasattr(self, "extra_list"):
            # get any extra data to be passed to the list data object
            response.data.update(self.extra_list(request))
        return response

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, args, kwargs)
        content_type = self.get_content_type().id
        response.data.update({"content_type": content_type})
        return response

import django_filters
from django.db import models

from accounts.models import User, Role


class UserFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method="filter_search")
    role = django_filters.NumberFilter(method="filter_by_role")
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = User
        fields = ["search", "role", "is_active"]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            models.Q(username__icontains=value) |
            models.Q(full_name__icontains=value) |
            models.Q(phone__icontains=value)
        )

    def filter_by_role(self, queryset, name, role_id):
        return queryset.filter(roles__id=role_id)

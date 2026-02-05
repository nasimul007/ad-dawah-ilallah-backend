class InstitutionScopedQuerySetMixin:
    """
    Automatically filters queryset by user's institution.
    Superusers bypass institution filtering.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if user.is_superuser:
            return qs

        if hasattr(qs.model, "institution_id"):
            return qs.filter(institution=user.institution)

        return qs
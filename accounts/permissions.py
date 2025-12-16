from rest_framework.permissions import BasePermission


class HasPermissionCode(BasePermission):
    """
    Generic permission checker based on permission codes attached to user roles.

    Supported view attributes:

    - required_permission = "USER_MANAGEMENT"
      or required_permission = ["PERM_A", "PERM_B"]

    - required_permissions = {
          "GET": "USER_MANAGEMENT_VIEW",
          "POST": ["USER_MANAGEMENT_CREATE", "AUDIT_LOG"],
          "DELETE": "USER_MANAGEMENT_DELETE",
      }

    - permission_mode = "any" | "all"
      (default: "any")
    """

    default_permission_mode = "any"  # "any" or "all"

    def get_required_permissions(self, request, view):
        """
        Resolve a list of permission codes required for this request.
        """
        # 1) Per-method mapping takes priority if present
        mapping = getattr(view, "required_permissions", None)
        if mapping:
            value = mapping.get(request.method)
            if not value:
                return []

            if isinstance(value, str):
                return [value]
            return list(value)

        # 2) Fallback: single/global required_permission
        value = getattr(view, "required_permission", None)
        if not value:
            return []

        if isinstance(value, str):
            return [value]
        return list(value)

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        required_codes = self.get_required_permissions(request, view)

        # If no specific permission defined on the view → just authenticated is enough
        if not required_codes:
            return False

        # Determine mode: "any" / "all"
        mode = getattr(view, "permission_mode", self.default_permission_mode)

        if mode == "all":
            return all(user.has_permission_code(code) for code in required_codes)

        # default: require at least one
        return any(user.has_permission_code(code) for code in required_codes)

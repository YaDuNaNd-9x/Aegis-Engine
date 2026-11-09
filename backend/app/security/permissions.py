from enum import Enum


class Role(str, Enum):
    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMIN = "admin"


class PermissionDenied(Exception):
    """Raised when an operation is not permitted."""


class ApprovalRequired(Exception):
    """Raised when an operation requires explicit human approval."""


ROLE_PERMISSIONS = {
    Role.VIEWER: {
        "chat",
        "document_search",
        "document_view",
        "audit_view",
        "report_view",
    },

    Role.OPERATOR: {
        "chat",
        "document_search",
        "document_view",
        "document_upload",
        "data_analysis",
        "report_view",
        "report_generate",
        "audit_view",
    },

    Role.ADMIN: {
        "chat",
        "document_search",
        "document_view",
        "document_upload",
        "data_analysis",
        "report_view",
        "report_generate",
        "audit_view",
        "audit_manage",
        "system_manage",
    },
}

SENSITIVE_ACTIONS = {
    "document_delete",
    "report_delete",
    "audit_manage",
    "system_manage",
    "plant_control",
    "configuration_change",
}


def check_permission(
    role: Role | str,
    action: str,
) -> bool:
    """
    Check whether a role is permitted to perform an action.
    """

    try:
        normalized_role = Role(role)
    except ValueError:
        raise PermissionDenied("Unknown user role.")

    permitted_actions = ROLE_PERMISSIONS.get(
        normalized_role,
        set(),
    )

    if action not in permitted_actions:
        raise PermissionDenied(
            f"Role '{normalized_role.value}' cannot perform '{action}'."
        )

    return True


def require_permission(
    role: Role | str,
    action: str,
) -> None:
    check_permission(role, action)


def requires_human_approval(action: str) -> bool:
    return action in SENSITIVE_ACTIONS


def require_human_approval(
    action: str,
    approved: bool = False,
) -> None:
    """
    Gate sensitive operations behind an explicit approval decision.

    The caller must obtain approval through a trusted user interaction.
    """

    if requires_human_approval(action) and not approved:
        raise ApprovalRequired(
            f"Human approval is required before '{action}'."
        )


def authorize_action(
    role: Role | str,
    action: str,
    approved: bool = False,
) -> None:
    """
    Combined permission and approval check.
    """

    require_permission(role, action)
    require_human_approval(action, approved)
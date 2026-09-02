import pytest
from unittest.mock import MagicMock

from app.core.exceptions import ForbiddenError
from app.models.group import GroupMemberRole
from app.schemas.group import GroupMemberAdd
from app.services.group_service import GroupService


def test_non_admin_cannot_add_group_member():
    group_repo = MagicMock()
    user_repo = MagicMock()
    group_repo.get_member.return_value = MagicMock(role=GroupMemberRole.MEMBER)
    service = GroupService(group_repo, user_repo)

    with pytest.raises(ForbiddenError, match="admins"):
        service.add_member(1, GroupMemberAdd(identifier="friend@example.com"), 10)

    user_repo.get_by_email.assert_not_called()

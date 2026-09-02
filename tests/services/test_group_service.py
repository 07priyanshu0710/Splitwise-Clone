import pytest
from unittest.mock import MagicMock
from types import SimpleNamespace

from app.core.exceptions import BusinessLogicError, ForbiddenError
from app.models.group import GroupMemberRole
from app.schemas.group import GroupCreate, GroupMemberAdd
from app.services.group_service import GroupService


def test_non_admin_cannot_add_group_member():
    group_repo = MagicMock()
    user_repo = MagicMock()
    group_repo.get_member.return_value = MagicMock(role=GroupMemberRole.MEMBER)
    service = GroupService(group_repo, user_repo)

    with pytest.raises(ForbiddenError, match="admins"):
        service.add_member(1, GroupMemberAdd(identifier="friend@example.com"), 10)

    user_repo.get_by_email.assert_not_called()


def test_create_group_commits_group_and_admin_membership_once():
    group_repo = MagicMock()
    user_repo = MagicMock()
    group = SimpleNamespace(id=7)
    group_repo.create_group.return_value = group
    group_repo.get_with_members.return_value = group
    service = GroupService(group_repo, user_repo)

    result = service.create_group(GroupCreate(name="Trip"), user_id=10)

    assert result is group
    group_repo.create_group.assert_called_once()
    group_repo.add_member.assert_called_once_with(7, 10, GroupMemberRole.ADMIN)
    group_repo.db.commit.assert_called_once_with()


def test_create_group_rolls_back_if_admin_membership_fails():
    group_repo = MagicMock()
    user_repo = MagicMock()
    group_repo.create_group.return_value = SimpleNamespace(id=7)
    group_repo.add_member.side_effect = RuntimeError("insert failed")
    service = GroupService(group_repo, user_repo)

    with pytest.raises(BusinessLogicError, match="Failed to create group"):
        service.create_group(GroupCreate(name="Trip"), user_id=10)

    group_repo.db.rollback.assert_called_once_with()
    group_repo.db.commit.assert_not_called()

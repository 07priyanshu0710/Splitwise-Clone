from typing import List
from sqlalchemy.exc import IntegrityError

from app.repositories.group_repository import GroupRepository
from app.repositories.user_repository import UserRepository
from app.schemas.group import GroupCreate, GroupMemberAdd
from app.models.group import Group, GroupMemberRole
from app.core.exceptions import BusinessLogicError, NotFoundError, ForbiddenError
from app.core.logging_config import LoggerMixin

class GroupService(LoggerMixin):
    def __init__(self, repository: GroupRepository, user_repository: UserRepository):
        self.repository = repository
        self.user_repository = user_repository

    def create_group(self, group_in: GroupCreate, user_id: int) -> Group:
        self.logger.info(f"Creating group {group_in.name} by user {user_id}")
        group_data = group_in.model_dump()
        group_data["created_by_id"] = user_id
        try:
            group = self.repository.create_group(group_data)
            self.repository.add_member(group.id, user_id, GroupMemberRole.ADMIN)
            group_id = group.id
            self.repository.db.commit()
        except Exception as exc:
            self.repository.db.rollback()
            self.logger.exception("Failed to create group")
            raise BusinessLogicError("Failed to create group") from exc

        self.logger.info(f"Group {group_id} created")
        return self.repository.get_with_members(group_id)

    def get_group(self, group_id: int, user_id: int) -> Group:
        member = self.repository.get_member(group_id, user_id)
        if not member:
            self.logger.warning(f"User {user_id} tried to access group {group_id} without being a member")
            raise ForbiddenError("Not a member of this group")

        group = self.repository.get_with_members(group_id)
        if not group:
            raise NotFoundError("Group not found")
        return group

    def get_user_groups(self, user_id: int) -> List[Group]:
        return self.repository.get_user_groups(user_id)

    def add_member(self, group_id: int, member_in: GroupMemberAdd, requester_id: int):
        self.logger.info(f"User {requester_id} adding member {member_in.identifier} to group {group_id}")
        requester = self.repository.get_member(group_id, requester_id)
        if not requester:
            raise ForbiddenError("Not a member of this group")
        if requester.role != GroupMemberRole.ADMIN:
            raise ForbiddenError("Only group admins can add members")

        identifier = member_in.identifier.strip()
        if '@' in identifier:
            user_to_add = self.user_repository.get_by_email(identifier)
        else:
            user_to_add = self.user_repository.get_by_mobile_number(identifier)

        if not user_to_add:
            self.logger.warning(f"User identifier {identifier} not found")
            raise NotFoundError(f"No registered user found with identifier '{identifier}'. They must register first.")

        existing_member = self.repository.get_member(group_id, user_to_add.id)
        if existing_member:
            raise BusinessLogicError("User is already a member of this group")

        try:
            self.repository.add_member(group_id, user_to_add.id, GroupMemberRole.MEMBER)
            self.repository.db.commit()
        except IntegrityError as exc:
            self.repository.db.rollback()
            raise BusinessLogicError("User is already a member of this group") from exc
        except Exception:
            self.repository.db.rollback()
            raise

        self.logger.info(f"User {user_to_add.id} added to group {group_id}")
        return self.repository.get_with_members(group_id)

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List

from app.repositories.group_repository import GroupRepository
from app.repositories.user_repository import UserRepository
from app.schemas.group import GroupCreate, GroupMemberAdd
from app.models.group import Group, GroupMemberRole

class GroupService:
    def __init__(self, db: Session):
        self.repository = GroupRepository(db)
        self.user_repository = UserRepository(db)

    def create_group(self, group_in: GroupCreate, user_id: int) -> Group:
        group_data = group_in.model_dump()
        group_data["created_by_id"] = user_id
        group = self.repository.create(group_data)
        self.repository.add_member(group.id, user_id, GroupMemberRole.ADMIN)
        return self.repository.get_with_members(group.id)

    def get_group(self, group_id: int, user_id: int) -> Group:
        member = self.repository.get_member(group_id, user_id)
        if not member:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this group")

        group = self.repository.get_with_members(group_id)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
        return group

    def get_user_groups(self, user_id: int) -> List[Group]:
        return self.repository.get_user_groups(user_id)

    def add_member(self, group_id: int, member_in: GroupMemberAdd, requester_id: int):
        requester = self.repository.get_member(group_id, requester_id)
        if not requester:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this group")

        identifier = member_in.identifier.strip()
        if '@' in identifier:
            user_to_add = self.user_repository.get_by_email(identifier)
            if not user_to_add:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No registered user found with email '{identifier}'. They must register first."
                )
        else:
            user_to_add = self.user_repository.get_by_mobile_number(identifier)
            if not user_to_add:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No registered user found with mobile number '{identifier}'. They must register first."
                )

        existing_member = self.repository.get_member(group_id, user_to_add.id)
        if existing_member:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member of this group")

        self.repository.add_member(group_id, user_to_add.id, GroupMemberRole.MEMBER)
        return self.repository.get_with_members(group_id)

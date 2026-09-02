from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Set
from app.repositories.base import BaseRepository
from app.models.group import Group, GroupMember, GroupMemberRole

class GroupRepository(BaseRepository[Group]):
    def __init__(self, db: Session):
        super().__init__(Group, db)

    def get_with_members(self, id: int) -> Optional[Group]:
        return self.db.query(self.model).options(
            joinedload(Group.members).joinedload(GroupMember.user)
        ).filter(self.model.id == id).first()

    def get_user_groups(self, user_id: int) -> List[Group]:
        return self.db.query(Group).join(GroupMember).filter(GroupMember.user_id == user_id).all()

    def create_group(self, obj_in: dict) -> Group:
        group = Group(**obj_in)
        self.db.add(group)
        self.db.flush()
        return group

    def add_member(self, group_id: int, user_id: int, role: GroupMemberRole = GroupMemberRole.MEMBER) -> GroupMember:
        member = GroupMember(group_id=group_id, user_id=user_id, role=role)
        self.db.add(member)
        self.db.flush()
        return member

    def get_member(self, group_id: int, user_id: int) -> Optional[GroupMember]:
        return self.db.query(GroupMember).filter(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id
        ).first()

    def get_member_user_ids(self, group_id: int, user_ids: Set[int]) -> Set[int]:
        if not user_ids:
            return set()
        rows = self.db.query(GroupMember.user_id).filter(
            GroupMember.group_id == group_id,
            GroupMember.user_id.in_(user_ids),
        ).all()
        return {row[0] for row in rows}

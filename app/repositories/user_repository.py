
from sqlalchemy.orm import Session
from typing import Optional
from app.repositories.base import BaseRepository
from app.models.user import User

class UserRepository(BaseRepository[User]):
    def __init__(self, db_session: Session):
        super().__init__(User, db_session)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_mobile_number(self, mobile_number: str) -> Optional[User]:
        return self.db.query(User).filter(User.mobile_number == mobile_number).first()

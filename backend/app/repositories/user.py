from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.user import User
from typing import Optional
import datetime

class UserRepository(BaseRepository):
    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def update_last_login(self, user: User) -> None:
        user.last_login_at = datetime.datetime.utcnow()
        self.db.commit()

    def create(self, username: str, password_hash: str) -> User:
        user = User(
            username=username,
            password_hash=password_hash
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

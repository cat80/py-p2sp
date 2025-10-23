from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    status = Column(Integer, nullable=False, default=1)  # 1: normal, 0: disabled
    is_admin = Column(Boolean, nullable=False, default=False)
    auth_token = Column(String, nullable=True, index=True)
    create_time = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

class Group(Base):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_name = Column(String, nullable=False)
    creator_user_id = Column(Integer, ForeignKey('users.id'))
    status = Column(Integer, nullable=False, default=1)  # 1: normal, 0: banned
    create_time = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    creator = relationship("User")
    __table_args__ = (UniqueConstraint('group_name', 'creator_user_id', name='_group_creator_uc'),)

class GroupMember(Base):
    __tablename__ = 'group_members'
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey('groups.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    role = Column(Integer, nullable=False, default=1)  # 0: creator, 1: member
    join_time = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    group = relationship("Group")
    user = relationship("User")
    __table_args__ = (UniqueConstraint('group_id', 'user_id', name='_group_user_uc'),)

class UserFriend(Base):
    __tablename__ = 'user_friends'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id_a = Column(Integer, ForeignKey('users.id'))
    user_id_b = Column(Integer, ForeignKey('users.id'))
    create_time = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    user_a = relationship("User", foreign_keys=[user_id_a])
    user_b = relationship("User", foreign_keys=[user_id_b])
    __table_args__ = (UniqueConstraint('user_id_a', 'user_id_b', name='_user_friends_uc'),)

class OfflineMessage(Base):
    __tablename__ = 'offline_messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    recipient_user_id = Column(Integer, ForeignKey('users.id'), index=True)
    message_payload = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    recipient = relationship("User")

class UserLoginLog(Base):
    __tablename__ = 'user_login_log'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    username = Column(String, nullable=False)
    login_time = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    login_ip = Column(String, nullable=True)

    user = relationship("User")

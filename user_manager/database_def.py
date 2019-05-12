from sqlalchemy import Column, DateTime, String, BigInteger, Boolean, ForeignKey, func, create_engine, and_, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref

Base = declarative_base()
engine = create_engine("mysql://root:@localhost/user_manager")
session = sessionmaker()
session.configure(bind=engine)
Base.metadata.create_all(engine)


class User(Base):
    __tablename__ = 'users'
    id = Column(BigInteger, primary_key=True)
    name = Column(String(255), unique=True)
    email = Column(String(255))
    password = Column(String(128))
    salt = Column(String(128))
    currentID = Column(String(128), default="")
    validUntilID = Column(DateTime, default=func.now())
    rights = Column(BigInteger, default=0)
    confirmed = Column(Boolean, default=False)
    friends1 = relationship("UserFriend", back_populates="user1", primaryjoin="and_(User.id==UserFriend.user1_id)", cascade="delete")
    friends2 = relationship("UserFriend", back_populates="user2", primaryjoin="and_(User.id==UserFriend.user2_id)", cascade="delete")
    messagesReceived = relationship("Message", back_populates="receiver", primaryjoin="and_(User.id==Message.receiver_id)", cascade="delete")
    messagesSent = relationship("Message", back_populates="sender", primaryjoin="and_(User.id==Message.sender_id)")
    teamUser = relationship("TeamUser", back_populates="user", cascade="delete")


class UserFriend(Base):
    __tablename__ = 'user_friends'
    id = Column(BigInteger, primary_key=True)
    user1_id = Column(BigInteger, ForeignKey('users.id'))
    user2_id = Column(BigInteger, ForeignKey('users.id'))
    startTime = Column(DateTime, default=func.now())
    accepted = Column(Boolean, default=False)
    user1 = relationship('User', back_populates="friends1", primaryjoin="and_(User.id==UserFriend.user1_id)")
    user2 = relationship('User', back_populates="friends2", primaryjoin="and_(User.id==UserFriend.user2_id)")


class Message(Base):
    __tablename__ = 'messages'
    id = Column(BigInteger, primary_key=True)
    receiver_id = Column(BigInteger, ForeignKey('users.id'))
    sender_id = Column(BigInteger, ForeignKey('users.id'))
    message = Column(String(1000))
    sentTime = Column(DateTime, default=func.now())
    receiverRead = Column(Boolean, default=False)
    receiver = relationship('User', back_populates="messagesReceived", primaryjoin="and_(User.id==Message.receiver_id)")
    sender = relationship('User', back_populates="messagesSent", primaryjoin="and_(User.id==Message.sender_id)")


class Team(Base):
    __tablename__ = 'teams'
    id = Column(BigInteger, primary_key=True)
    name = Column(String(255))
    teamUser = relationship("TeamUser", back_populates="team", cascade="delete")


class TeamUser(Base):
    __tablename__ = 'team_users'
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    team_id = Column(BigInteger, ForeignKey('teams.id'))
    role = Column(BigInteger, default=0)
    enrollTime = Column(DateTime, default=func.now())
    user = relationship('User', back_populates="teamUser")
    team = relationship('Team', back_populates="teamUser")



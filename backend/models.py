# backend/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base
from typing import Optional

Base = declarative_base()

# Table d'association pour la relation Many-to-Many entre User et Board (collaborateurs)
board_members = Table(
    'board_members',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('board_id', Integer, ForeignKey('boards.id', ondelete='CASCADE'), primary_key=True),
    Column('role', String(20), default='member', nullable=False)  # 'owner', 'admin', 'member'
)

# Table d'association pour la relation Many-to-Many entre Card et Label
card_labels = Table(
    'card_labels',
    Base.metadata,
    Column('card_id', Integer, ForeignKey('cards.id', ondelete='CASCADE'), primary_key=True),
    Column('label_id', Integer, ForeignKey('labels.id', ondelete='CASCADE'), primary_key=True)
)

# Table d'association pour la relation Many-to-Many entre User et Card (assignation)
card_members = Table(
    'card_members',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('card_id', Integer, ForeignKey('cards.id', ondelete='CASCADE'), primary_key=True)
)


class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(100))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relations
    boards_owned: Mapped[list["Board"]] = relationship(
        "Board", 
        back_populates="owner", 
        foreign_keys="Board.owner_id",
        cascade="all, delete-orphan"
    )
    boards: Mapped[list["Board"]] = relationship(
        "Board", 
        secondary=board_members, 
        back_populates="members"
    )
    cards_created: Mapped[list["Card"]] = relationship(
        "Card", 
        back_populates="author", 
        foreign_keys="Card.author_id"
    )
    cards_assigned: Mapped[list["Card"]] = relationship(
        "Card", 
        secondary=card_members, 
        back_populates="members"
    )
    comments: Mapped[list["Comment"]] = relationship(
        "Comment", 
        back_populates="author",
        cascade="all, delete-orphan"
    )


class Board(Base):
    __tablename__ = 'boards'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    background_color: Mapped[str] = mapped_column(String(7), default="#FFFFFF", nullable=False)  # Hex color
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Clés étrangères
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relations
    owner: Mapped["User"] = relationship(
        "User", 
        back_populates="boards_owned", 
        foreign_keys=[owner_id]
    )
    members: Mapped[list["User"]] = relationship(
        "User", 
        secondary=board_members, 
        back_populates="boards"
    )
    lists: Mapped[list["List"]] = relationship(
        "List", 
        back_populates="board", 
        cascade="all, delete-orphan"
    )
    labels: Mapped[list["Label"]] = relationship(
        "Label", 
        back_populates="board", 
        cascade="all, delete-orphan"
    )


class List(Base):
    __tablename__ = 'lists'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Ordre dans le board
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Clés étrangères
    board_id: Mapped[int] = mapped_column(Integer, ForeignKey('boards.id', ondelete='CASCADE'), nullable=False)
    
    # Relations
    board: Mapped["Board"] = relationship("Board", back_populates="lists")
    cards: Mapped[list["Card"]] = relationship(
        "Card", 
        back_populates="list", 
        cascade="all, delete-orphan"
    )


class Card(Base):
    __tablename__ = 'cards'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Ordre dans la liste
    due_date: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Clés étrangères
    list_id: Mapped[int] = mapped_column(Integer, ForeignKey('lists.id', ondelete='CASCADE'), nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relations
    list: Mapped["List"] = relationship("List", back_populates="cards")
    author: Mapped["User"] = relationship(
        "User", 
        back_populates="cards_created", 
        foreign_keys=[author_id]
    )
    members: Mapped[list["User"]] = relationship(
        "User", 
        secondary=card_members, 
        back_populates="cards_assigned"
    )
    labels: Mapped[list["Label"]] = relationship(
        "Label", 
        secondary=card_labels, 
        back_populates="cards"
    )
    comments: Mapped[list["Comment"]] = relationship(
        "Comment", 
        back_populates="card",
        cascade="all, delete-orphan"
    )


class Label(Base):
    __tablename__ = 'labels'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)  # Format hexadécimal : #FF5733
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Clés étrangères
    board_id: Mapped[int] = mapped_column(Integer, ForeignKey('boards.id', ondelete='CASCADE'), nullable=False)
    
    # Relations
    board: Mapped["Board"] = relationship("Board", back_populates="labels")
    cards: Mapped[list["Card"]] = relationship(
        "Card", 
        secondary=card_labels, 
        back_populates="labels"
    )


class Comment(Base):
    __tablename__ = 'comments'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Clés étrangères
    card_id: Mapped[int] = mapped_column(Integer, ForeignKey('cards.id', ondelete='CASCADE'), nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Relations
    card: Mapped["Card"] = relationship("Card", back_populates="comments")
    author: Mapped["User"] = relationship("User", back_populates="comments")
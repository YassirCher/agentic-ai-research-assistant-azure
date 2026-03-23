from datetime import datetime
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel, Session, create_engine, select
import os

# Configuration du chemin de la base de données
# En local : ./db_data/chats.db
# En Docker : /app/db/chats.db (via volume)
DB_DIR = "db_data"
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

sqlite_url = f"sqlite:///{DB_DIR}/chats.db"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

class Chat(SQLModel, table=True):
    id: str = Field(primary_key=True)
    title: str = Field(default="Nouveau Chat")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    messages: List["Message"] = Relationship(back_populates="chat", cascade_delete=True)

class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    chat_id: str = Field(foreign_key="chat.id")
    role: str # 'user' or 'ai'
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    chat: Chat = Relationship(back_populates="messages")

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

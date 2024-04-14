from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.mysql import JSON
from config import config

DATABASE_URL = f"mysql+pymysql://{config['mysql']['user']}:{config['mysql']['password']}@127.0.0.1/takway?charset=utf8mb4"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class CharacterModel(Base):
    __tablename__ = "characters"

    char_id = Column(Integer, primary_key=True, index=True)
    voice_id = Column(Integer)
    char_name = Column(String(255))
    wakeup_words = Column(String(255))
    world_scenario = Column(Text)
    description = Column(Text)
    emojis = Column(JSON)
    dialogues = Column(Text)
    
    class Config:
        orm_mode = True
        from_attributes = True

Base.metadata.create_all(bind=engine)

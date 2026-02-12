import logging
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from config import DATABASE_URL

logger = logging.getLogger(__name__)

# ================= DATABASE BASE =================
Base = declarative_base()

# ================= MODELS =================
class Movie(Base):
    """Kinolar jadvali"""
    __tablename__ = "movies"
    
    id = Column(Integer, primary_key=True)
    code = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=False)
    file_id = Column(String(255), nullable=False)
    file_type = Column(String(20), default="video")
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<Movie(code={self.code}, name='{self.name}')>"

class User(Base):
    """Foydalanuvchilar jadvali"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(20), unique=True, nullable=False, index=True)
    username = Column(String(255))
    first_name = Column(String(255))
    joined_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, username='{self.username}')>"

# ================= DATABASE MANAGER =================
class Database:
    """PostgreSQL database manager"""
    def __init__(self, database_url: str):
        self.engine = create_engine(
            database_url,
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.create_tables()
    
    def create_tables(self):
        """Jadvallarni yaratish"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Database jadvallar tayyorlandi")
        except Exception as e:
            logger.error(f"❌ Database xatosi: {e}")
            raise
    
    def get_session(self) -> Session:
        return self.SessionLocal()

    # ================= KINO OPERATIONS =================
    def add_movie(self, code: int, name: str, category: str, description: str, file_id: str, file_type: str = "video") -> bool:
        try:
            session = self.get_session()
            movie = Movie(code=code, name=name, category=category, description=description, file_id=file_id, file_type=file_type)
            session.add(movie)
            session.commit()
            session.close()
            logger.info(f"✅ Kino qo'shildi: {name} (Kod: {code})")
            return True
        except Exception as e:
            logger.error(f"❌ Kino qo'shishda xatolik: {e}")
            return False

    def get_movie_by_code(self, code: int):
        try:
            session = self.get_session()
            movie = session.query(Movie).filter_by(code=code).first()
            session.close()
            return movie
        except Exception as e:
            logger.error(f"❌ Kino qidirish xatosi: {e}")
            return None

    def delete_movie(self, code: int) -> bool:
        try:
            session = self.get_session()
            movie = session.query(Movie).filter_by(code=code).first()
            if movie:
                session.delete(movie)
                session.commit()
                session.close()
                logger.info(f"✅ Kino o'chirildi: {movie.name}")
                return True
            session.close()
            return False
        except Exception as e:
            logger.error(f"❌ Kino o'chirish xatosi: {e}")
            return False

    def get_all_movies(self):
        try:
            session = self.get_session()
            movies = session.query(Movie).all()
            session.close()
            return movies
        except Exception as e:
            logger.error(f"❌ Barcha kinolar xatosi: {e}")
            return []

    # ================= USER OPERATIONS =================
    def add_user(self, user_id: int, username: str = None, first_name: str = None) -> bool:
        try:
            session = self.get_session()
            existing = session.query(User).filter_by(user_id=str(user_id)).first()
            if existing:
                session.close()
                return False
            user = User(user_id=str(user_id), username=username, first_name=first_name)
            session.add(user)
            session.commit()
            session.close()
            logger.info(f"✅ Foydalanuvchi qo'shildi: {first_name} ({user_id})")
            return True
        except Exception as e:
            logger.error(f"❌ Foydalanuvchi qo'shish xatosi: {e}")
            return False

    def user_exists(self, user_id: int) -> bool:
        try:
            session = self.get_session()
            exists = session.query(User).filter_by(user_id=str(user_id)).first() is not None
            session.close()
            return exists
        except Exception as e:
            logger.error(f"❌ Foydalanuvchi tekshirish xatosi: {e}")
            return False

    def get_all_users(self):
        try:
            session = self.get_session()
            users = session.query(User).all()
            session.close()
            return users
        except Exception as e:
            logger.error(f"❌ Barcha foydalanuvchilar xatosi: {e}")
            return []

# ================= GLOBAL DATABASE INSTANCE =================
db = Database(DATABASE_URL)

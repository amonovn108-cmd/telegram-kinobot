import logging
from sqlalchemy import create_engine, Column, Integer, String, Text, JSON, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from config import DATABASE_URL
import json

logger = logging.getLogger(__name__)

Base = declarative_base()


# ==================== MODELLAR ====================
class Movie(Base):
    """Kinolar jadvali"""
    __tablename__ = "movies"
    
    id = Column(Integer, primary_key=True)
    code = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=False)
    file_id = Column(String(255), nullable=True)  # Bitta video uchun
    file_type = Column(String(20), default="video")
    parts = Column(JSON, nullable=True)  # Serial qismlari uchun [{"name": "1-qism", "file_id": "..."}]
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<Movie(code={self.code}, name='{self.name}')>"


class User(Base):
    """Foydalanuvchilar jadvali"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(20), unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    joined_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<User(user_id={self.user_id})>"


# ==================== DATABASE MANAGER ====================
class Database:
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
    
    # ==================== KINO OPERATIONS ====================
    
    def add_movie(self, code: int, name: str, category: str, description: str, 
                  file_id: str = None, file_type: str = "video", parts: list = None) -> bool:
        """Yangi kino qo'shish"""
        try:
            session = self.get_session()
            
            movie = Movie(
                code=code,
                name=name,
                category=category,
                description=description,
                file_id=file_id,
                file_type=file_type,
                parts=parts
            )
            
            session.add(movie)
            session.commit()
            session.close()
            
            logger.info(f"✅ Kino qo'shildi: {name} (Kod: {code})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Kino qo'shishda xatolik: {e}")
            return False
    
    def add_serial(self, code: int, name: str, category: str, description: str, parts: list) -> bool:
        """Serial qo'shish (qismlar bilan)"""
        return self.add_movie(
            code=code,
            name=name,
            category=category,
            description=description,
            parts=parts,
            file_type="serial"
        )
    
    def get_movie_by_code(self, code: int) -> dict:
        """Kod bo'yicha kino olish"""
        try:
            session = self.get_session()
            movie = session.query(Movie).filter_by(code=code).first()
            session.close()
            
            if movie:
                return self._movie_to_dict(movie)
            return None
            
        except Exception as e:
            logger.error(f"❌ Kino qidirish xatosi: {e}")
            return None
    
    def get_movies_by_category(self, category: str) -> list:
        """Kategoriya bo'yicha kinolarni olish"""
        try:
            session = self.get_session()
            movies = session.query(Movie).filter_by(category=category).order_by(Movie.code).all()
            session.close()
            
            return [self._movie_to_dict(m) for m in movies]
            
        except Exception as e:
            logger.error(f"❌ Kategoriya bo'yicha kinolar xatosi: {e}")
            return []
    
    def search_movies_by_name(self, name: str, category: str = None) -> list:
        """Nom bo'yicha kino qidirish"""
        try:
            session = self.get_session()
            query = session.query(Movie).filter(Movie.name.ilike(f'%{name}%'))
            
            if category:
                query = query.filter_by(category=category)
            
            movies = query.order_by(Movie.code).all()
            session.close()
            
            return [self._movie_to_dict(m) for m in movies]
            
        except Exception as e:
            logger.error(f"❌ Kino qidirish xatosi: {e}")
            return []
    
    def get_all_movies(self) -> list:
        """Barcha kinolarni olish"""
        try:
            session = self.get_session()
            movies = session.query(Movie).order_by(Movie.category, Movie.code).all()
            session.close()
            
            return [self._movie_to_dict(m) for m in movies]
            
        except Exception as e:
            logger.error(f"❌ Barcha kinolar xatosi: {e}")
            return []
    
    def delete_movie(self, code: int) -> bool:
        """Kinoni o'chirish"""
        try:
            session = self.get_session()
            movie = session.query(Movie).filter_by(code=code).first()
            
            if movie:
                session.delete(movie)
                session.commit()
                session.close()
                logger.info(f"✅ Kino o'chirildi: {code}")
                return True
            
            session.close()
            return False
            
        except Exception as e:
            logger.error(f"❌ Kino o'chirish xatosi: {e}")
            return False
    
    def get_movie_count_by_category(self) -> dict:
        """Kategoriyalar bo'yicha kino soni"""
        try:
            session = self.get_session()
            from sqlalchemy import func
            
            result = session.query(
                Movie.category, 
                func.count(Movie.id)
            ).group_by(Movie.category).all()
            
            session.close()
            
            return {cat: count for cat, count in result}
            
        except Exception as e:
            logger.error(f"❌ Kino soni xatosi: {e}")
            return {}
    
    # ==================== FOYDALANUVCHI OPERATIONS ====================
    
    def add_user(self, user_id: str, username: str = None, first_name: str = None) -> bool:
        """Yangi foydalanuvchi qo'shish"""
        try:
            session = self.get_session()
            
            # Mavjudligini tekshirish
            existing = session.query(User).filter_by(user_id=user_id).first()
            
            if existing:
                session.close()
                return False
            
            user = User(
                user_id=user_id,
                username=username,
                first_name=first_name
            )
            
            session.add(user)
            session.commit()
            session.close()
            
            logger.info(f"✅ Foydalanuvchi qo'shildi: {first_name} ({user_id})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Foydalanuvchi qo'shish xatosi: {e}")
            return False
    
    def get_all_users(self) -> list:
        """Barcha foydalanuvchilarni olish"""
        try:
            session = self.get_session()
            users = session.query(User).order_by(User.joined_at.desc()).all()
            session.close()
            
            return [self._user_to_dict(u) for u in users]
            
        except Exception as e:
            logger.error(f"❌ Barcha foydalanuvchilar xatosi: {e}")
            return []
    
    def get_user_count(self) -> int:
        """Foydalanuvchilar soni"""
        try:
            session = self.get_session()
            count = session.query(User).count()
            session.close()
            return count
        except Exception as e:
            logger.error(f"❌ Foydalanuvchilar soni xatosi: {e}")
            return 0
    
    def get_recent_users(self, limit: int = 10) -> list:
        """Oxirgi qo'shilgan foydalanuvchilar"""
        try:
            session = self.get_session()
            users = session.query(User).order_by(User.joined_at.desc()).limit(limit).all()
            session.close()
            
            return [self._user_to_dict(u) for u in users]
            
        except Exception as e:
            logger.error(f"❌ Oxirgi foydalanuvchilar xatosi: {e}")
            return []
    
    def user_exists(self, user_id: str) -> bool:
        """Foydalanuvchi mavjudligini tekshirish"""
        try:
            session = self.get_session()
            exists = session.query(User).filter_by(user_id=user_id).first() is not None
            session.close()
            return exists
        except Exception as e:
            logger.error(f"❌ Foydalanuvchi tekshirish xatosi: {e}")
            return False
    
    # ==================== YORDAMCHI FUNKSIYALAR ====================
    
    def _movie_to_dict(self, movie) -> dict:
        """Movie obyektini dict ga o'girish"""
        return {
            'id': movie.id,
            'code': movie.code,
            'name': movie.name,
            'category': movie.category,
            'description': movie.description,
            'file_id': movie.file_id,
            'file_type': movie.file_type,
            'parts': movie.parts if movie.parts else [],
            'created_at': movie.created_at
        }
    
    def _user_to_dict(self, user) -> dict:
        """User obyektini dict ga o'girish"""
        return {
            'id': user.id,
            'user_id': user.user_id,
            'username': user.username,
            'first_name': user.first_name,
            'joined_at': user.joined_at
        }


# ==================== GLOBAL DATABASE INSTANCE ====================
db = Database(DATABASE_URL)

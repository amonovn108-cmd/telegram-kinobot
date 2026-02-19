import logging
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, JSON, DateTime, BigInteger, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from config import DATABASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

# ================== MODELLAR ==================

class Movie(Base):
    """Kinolar jadvali"""
    __tablename__ = 'movies'

    id = Column(Integer, primary_key=True)
    code = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=False)
    file_id = Column(String(255), nullable=True)      # Bitta video uchun
    file_type = Column(String(20), default="video")    # video/document
    parts = Column(JSON, nullable=True)               # Serial qismlari [dict]
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Movie(code={self.code}, name='{self.name}')>"

class User(Base):
    """Foydalanuvchilar jadvali"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    user_id = Column(String(20), unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User(user_id={self.user_id})>"

# ================== DATABASE MANAGER ==================

class Database:
    def __init__(self, database_url: str):
        self.engine = create_engine(
            database_url, pool_size=10, max_overflow=20, pool_pre_ping=True, echo=False
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.create_tables()
        logger.info("✅ Database manager ishga tushdi.")

    def create_tables(self):
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Jadvallar yaratildi")
        except Exception as e:
            logger.error(f"❌ Jadvallar yaratishda xatolik: {e}")
            raise

    def get_session(self) -> Session:
        return self.SessionLocal()

    # ===== KINOLAR CRUD funktsiyalari =====

    def add_movie(self, code: int, name: str, category: str, description: str,
                  file_id: str = None, file_type: str = "video", parts: list = None) -> bool:
        """Kino yoki multfilm, yoki serial (parts=None bo‘lsa oddiy)"""
        try:
            session = self.get_session()
            movie = Movie(
                code=code, name=name, category=category, description=description,
                file_id=file_id, file_type=file_type, parts=parts
            )
            session.add(movie)
            session.commit()
            logger.info(f"✅ Kino qo'shildi: {name} (Kod: {code})")
            return True
        except Exception as e:
            logger.error(f"❌ Kino qo'shishda xatolik: {e}")
            return False
        finally:
            session.close()

    def add_serial(self, code: int, name: str, category: str, description: str, parts: list) -> bool:
        """Serial-kino qo‘shish”"""
        return self.add_movie(
            code=code, name=name, category=category, description=description, parts=parts, file_type="serial"
        )

    def get_movie_by_code(self, code: int) -> dict:
        """Kod bo‘yicha kino olish"""
        session = self.get_session()
        try:
            movie = session.query(Movie).filter_by(code=code).first()
            return self._movie_to_dict(movie) if movie else None
        except Exception as e:
            logger.error(f"❌ Kino qidirishda xatolik: {e}")
            return None
        finally:
            session.close()

    def get_movies_by_category(self, category: str) -> list:
        """Kategoriya bo‘yicha kinolarni olish"""
        session = self.get_session()
        try:
            movies = session.query(Movie).filter_by(category=category).order_by(Movie.code).all()
            return [self._movie_to_dict(m) for m in movies]
        except Exception as e:
            logger.error(f"❌ Kategoriya bo‘yicha kinolar xatosi: {e}")
            return []
        finally:
            session.close()

    def get_all_movies(self) -> list:
        """Barcha kinolarni olish"""
        session = self.get_session()
        try:
            movies = session.query(Movie).order_by(Movie.category, Movie.code).all()
            return [self._movie_to_dict(m) for m in movies]
        except Exception as e:
            logger.error(f"❌ Barcha kinolar xatosi: {e}")
            return []
        finally:
            session.close()

    def search_movies_by_name(self, name: str, category: str = None) -> list:
        """Ixtiyoriy matnga qarab qidirish (kategoriya bo‘lsa — unda)"""
        session = self.get_session()
        try:
            query = session.query(Movie).filter(Movie.name.ilike(f'%{name}%'))
            if category:
                query = query.filter_by(category=category)
            movies = query.order_by(Movie.code).all()
            return [self._movie_to_dict(m) for m in movies]
        except Exception as e:
            logger.error(f"❌ Kino qidirishda xatolik: {e}")
            return []
        finally:
            session.close()

    def delete_movie(self, code: int) -> bool:
        """Kino yoki serialni o‘chirish (all parts)"""
        session = self.get_session()
        try:
            movie = session.query(Movie).filter_by(code=code).first()
            if movie:
                session.delete(movie)
                session.commit()
                logger.info(f"✅ Kino o‘chirildi: {code}")
                return True
            logger.warning(f"🔍 O‘chiriladigan kino topilmadi: {code}")
            return False
        except Exception as e:
            logger.error(f"❌ O‘chirishda xatolik: {e}")
            return False
        finally:
            session.close()

    def get_movie_count_by_category(self) -> dict:
        """Kategoriya kesimida kino soni"""
        session = self.get_session()
        try:
            result = session.query(Movie.category, func.count(Movie.id)).group_by(Movie.category).all()
            return {cat: count for cat, count in result}
        except Exception as e:
            logger.error(f"❌ Kategoriya bo‘yicha kino sonini olishda xatolik: {e}")
            return {}
        finally:
            session.close()

    # ===== FOYDALANUVCHILAR CRUD funktsiyalari =====

    def add_user(self, user_id: str, username: str = None, first_name: str = None) -> bool:
        """Foydalanuvchini qo‘shish (yangi bo‘lsa)"""
        session = self.get_session()
        try:
            exists = session.query(User).filter_by(user_id=user_id).first()
            if exists:
                return False
            user = User(
                user_id=user_id, username=username, first_name=first_name
            )
            session.add(user)
            session.commit()
            logger.info(f"✅ Foydalanuvchi qo'shildi: {first_name} ({user_id})")
            return True
        except Exception as e:
            logger.error(f"❌ Foydalanuvchi qo‘shishda xatolik: {e}")
            return False
        finally:
            session.close()

    def get_all_users(self) -> list:
        """Barcha foydalanuvchilar ro‘yxati"""
        session = self.get_session()
        try:
            users = session.query(User).order_by(User.joined_at.desc()).all()
            return [self._user_to_dict(u) for u in users]
        except Exception as e:
            logger.error(f"❌ Foydalanuvchilarni olishda xatolik: {e}")
            return []
        finally:
            session.close()

    def get_user_count(self) -> int:
        """Foydalanuvchilar soni"""
        session = self.get_session()
        try:
            return session.query(User).count()
        except Exception as e:
            logger.error(f"❌ Foydalanuvchilar sonini olishda xatolik: {e}")
            return 0
        finally:
            session.close()

    def get_recent_users(self, limit: int = 10) -> list:
        """Oxirgi qo‘shilgan foydalanuvchilar"""
        session = self.get_session()
        try:
            users = session.query(User).order_by(User.joined_at.desc()).limit(limit).all()
            return [self._user_to_dict(u) for u in users]
        except Exception as e:
            logger.error(f"❌ Yaqinda qo‘shilgan foydalanuvchilarni olish xatosi: {e}")
            return []
        finally:
            session.close()

    def user_exists(self, user_id: str) -> bool:
        """Foydalanuvchi mavjudmi"""
        session = self.get_session()
        try:
            return session.query(User).filter_by(user_id=user_id).first() is not None
        except Exception as e:
            logger.error(f"❌ Foydalanuvchini tekshirishda xatolik: {e}")
            return False
        finally:
            session.close()

    # ======= YORDAMCHI FUNKSIYALAR =======

    def _movie_to_dict(self, movie: Movie) -> dict:
        """Movie modelini dictga aylantirish"""
        return {
            "id": movie.id,
            "code": movie.code,
            "name": movie.name,
            "category": movie.category,
            "description": movie.description,
            "file_id": movie.file_id,
            "file_type": movie.file_type,
            "parts": movie.parts if movie.parts else [],
            "created_at": movie.created_at
        }
    def _user_to_dict(self, user: User) -> dict:
        """User modelini dictga aylantirish"""
        return {
            "id": user.id,
            "user_id": user.user_id,
            "username": user.username,
            "first_name": user.first_name,
            "joined_at": user.joined_at
        }

# ========== GLOBAL INSTANCE ===========
db = Database(DATABASE_URL)

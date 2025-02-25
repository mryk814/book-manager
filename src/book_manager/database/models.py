import datetime
import os

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

# 書籍とタグの多対多関連付け
book_tag_association = Table(
    "book_tag_association",
    Base.metadata,
    Column("book_id", Integer, ForeignKey("books.id")),
    Column("tag_id", Integer, ForeignKey("tags.id")),
)

# 書籍とシリーズの多対多関連付け
book_series_association = Table(
    "book_series_association",
    Base.metadata,
    Column("book_id", Integer, ForeignKey("books.id")),
    Column("series_id", Integer, ForeignKey("series.id")),
)


class Book(Base):
    """書籍モデル"""

    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    author = Column(String)
    publisher = Column(String)
    publication_date = Column(String)
    file_path = Column(String, nullable=False, unique=True)
    thumbnail_path = Column(String)
    page_count = Column(Integer)
    current_page = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    comments = Column(String)
    is_read = Column(Boolean, default=False)
    reading_status = Column(String, default="未読")  # 未読, 読書中, 読了
    date_added = Column(DateTime, default=datetime.datetime.now)
    last_read = Column(DateTime)
    volume_number = Column(Integer)
    is_favorite = Column(Boolean, default=False)

    # リレーションシップ
    tags = relationship("Tag", secondary=book_tag_association, back_populates="books")
    series = relationship(
        "Series", secondary=book_series_association, back_populates="books"
    )
    custom_metadata = relationship(
        "CustomMetadata", back_populates="book", cascade="all, delete-orphan"
    )
    bookmarks = relationship(
        "Bookmark", back_populates="book", cascade="all, delete-orphan"
    )


class Tag(Base):
    """タグモデル"""

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    color = Column(String, default="#1E90FF")  # デフォルト色

    # リレーションシップ
    books = relationship("Book", secondary=book_tag_association, back_populates="tags")


class Series(Base):
    """シリーズモデル"""

    __tablename__ = "series"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)
    author = Column(String)
    publisher = Column(String)
    category = Column(String)  # 漫画, 小説, 技術書など

    # リレーションシップ
    books = relationship(
        "Book", secondary=book_series_association, back_populates="series"
    )


class Category(Base):
    """カテゴリモデル - 大きな分類（漫画棚、小説棚など）"""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)
    display_order = Column(Integer, default=0)

    # リレーションシップ
    views = relationship("View", back_populates="category")


class View(Base):
    """ビューモデル - 表示設定の保存"""

    __tablename__ = "views"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    view_type = Column(String, default="grid")  # grid, list, bookshelf
    sort_field = Column(String, default="title")
    sort_direction = Column(String, default="asc")
    filter_query = Column(String)
    category_id = Column(Integer, ForeignKey("categories.id"))

    # リレーションシップ
    category = relationship("Category", back_populates="views")


class CustomMetadata(Base):
    """カスタムメタデータモデル"""

    __tablename__ = "custom_metadata"

    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    key = Column(String, nullable=False)
    value = Column(String)

    # リレーションシップ
    book = relationship("Book", back_populates="custom_metadata")


class Bookmark(Base):
    """ブックマークモデル"""

    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    page = Column(Integer, nullable=False)
    name = Column(String)
    date_created = Column(DateTime, default=datetime.datetime.now)

    # リレーションシップ
    book = relationship("Book", back_populates="bookmarks")


def init_db(db_path):
    """データベースの初期化"""
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import enum

class TripStatus(str, enum.Enum):
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"

class PassType(str, enum.Enum):
    commuter = "commuter"  # 通勤定期
    student = "student"    # 通学定期

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    balance = Column(Numeric(10,2), default=0)
    qr_token = Column(String, unique=True, nullable=True, index=True)
    card_idm = Column(String, nullable=True)
    cards = relationship("Card", back_populates="user")
    passes = relationship("Pass", back_populates="user")

class Card(Base):
    __tablename__ = "cards"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    idm = Column(String, unique=True, nullable=True)
    qr_token = Column(String, unique=True, nullable=True)
    label = Column(String, nullable=True)
    user = relationship("User", back_populates="cards")
    trips = relationship("Trip", back_populates="card")

class Station(Base):
    __tablename__ = "stations"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)

class Gate(Base):
    __tablename__ = "gates"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False)
    station_id = Column(Integer, ForeignKey("stations.id"), nullable=True)
    name = Column(String, nullable=True)

class Trip(Base):
    __tablename__ = "trips"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=True)  # 顔認証の場合はNULL
    station_in = Column(String, nullable=True)
    gate_in = Column(String, nullable=True)
    station_out = Column(String, nullable=True)
    gate_out = Column(String, nullable=True)
    status = Column(Enum(TripStatus), default=TripStatus.in_progress)
    entered_at = Column(DateTime, default=datetime.utcnow)
    exited_at = Column(DateTime, nullable=True)
    device_id = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    used_pass_id = Column(Integer, ForeignKey("passes.id"), nullable=True)  # 使用した定期券ID
    fare_amount = Column(Numeric(10,2), nullable=True)  # 運賃額
    balance_before = Column(Numeric(10,2), nullable=True)  # 出場前の残高
    balance_after = Column(Numeric(10,2), nullable=True)  # 出場後の残高
    card = relationship("Card", back_populates="trips")

class Pass(Base):
    __tablename__ = "passes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pass_type = Column(Enum(PassType), nullable=False)
    station_from = Column(String, nullable=False)  # 定期券の開始駅
    station_to = Column(String, nullable=False)    # 定期券の終了駅
    valid_from = Column(DateTime, nullable=False)   # 有効期間開始日
    valid_until = Column(DateTime, nullable=False)  # 有効期間終了日
    is_active = Column(Integer, default=1)          # アクティブフラグ（1=有効、0=無効）
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="passes")

class Purchase(Base):
    __tablename__ = "purchases"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False)
    amount = Column(Numeric(10,2), nullable=False)  # 購入金額
    description = Column(String, nullable=True)      # 商品説明
    store_code = Column(String, nullable=True)       # 店舗コード（gate_codeを流用）
    balance_before = Column(Numeric(10,2), nullable=True)  # 決済前の残高
    balance_after = Column(Numeric(10,2), nullable=True)   # 決済後の残高
    device_id = Column(String, nullable=True)
    purchased_at = Column(DateTime, default=datetime.utcnow)
    timestamp = Column(DateTime, default=datetime.utcnow)

class FaceData(Base):
    __tablename__ = "face_data"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    face_encoding = Column(String, nullable=False)  # JSON形式で保存された顔エンコーディング
    registered_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Integer, default=1)  # 1=有効、0=無効

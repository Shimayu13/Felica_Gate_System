from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import enum

class TripStatus(str, enum.Enum):
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    balance = Column(Numeric(10,2), default=0)
    qr_token = Column(String, unique=True, nullable=True)
    card_idm = Column(String, unique=True, nullable=True)
    cards = relationship("Card", back_populates="user")
    face_data = relationship("FaceData", back_populates="user", uselist=False)

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
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False)
    station_in = Column(String, nullable=True)
    gate_in = Column(String, nullable=True)
    station_out = Column(String, nullable=True)
    gate_out = Column(String, nullable=True)
    status = Column(Enum(TripStatus), default=TripStatus.in_progress)
    entered_at = Column(DateTime, default=datetime.utcnow)
    exited_at = Column(DateTime, nullable=True)
    device_id = Column(String, nullable=True)
    used_pass_id = Column(Integer, ForeignKey("passes.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    card = relationship("Card", back_populates="trips")

class Purchase(Base):
    __tablename__ = "purchases"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False)
    amount = Column(Numeric(10,2), nullable=False)
    description = Column(String, nullable=True)
    store_code = Column(String, nullable=True)
    balance_before = Column(Numeric(10,2), nullable=True)
    balance_after = Column(Numeric(10,2), nullable=True)
    device_id = Column(String, nullable=True)
    purchased_at = Column(DateTime, default=datetime.utcnow)

class FaceData(Base):
    __tablename__ = "face_data"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    face_encoding = Column(String, nullable=False)
    registered_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)
    user = relationship("User", back_populates="face_data")

class Pass(Base):
    __tablename__ = "passes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pass_type = Column(String, nullable=False)
    station_from = Column(String, nullable=False)
    station_to = Column(String, nullable=False)
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=False)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

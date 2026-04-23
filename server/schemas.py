from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ScanRequest(BaseModel):
    scan_source: str
    card_idm: Optional[str] = None
    qr_token: Optional[str] = None
    face_image_base64: Optional[str] = None
    station_code: str
    gate_code: str
    timestamp: datetime
    device_id: str

class ScanResponseEntry(BaseModel):
    mode: str

class PurchaseRequest(BaseModel):
    scan_source: str
    card_idm: Optional[str] = None
    qr_token: Optional[str] = None
    amount: float
    description: str
    store_code: str
    device_id: str
    timestamp: Optional[datetime] = None

class FaceRegisterRequest(BaseModel):
    user_id: int
    face_image_base64: str

class FaceVerifyRequest(BaseModel):
    face_image_base64: str

class LoginRequest(BaseModel):
    qr_token: str

class ChargeRequest(BaseModel):
    user_id: int
    amount: float

class LinkCardRequest(BaseModel):
    qr_token: str
    card_idm: str

class PassCreateRequest(BaseModel):
    user_id: int
    pass_type: str
    station_from: str
    station_to: str
    valid_from: datetime
    valid_until: datetime

class ErrorResponse(BaseModel):
    status: str
    message: str

# ユーザー管理スキーマ
class UserCreate(BaseModel):
    name: str
    email: Optional[str] = None
    balance: Optional[float] = 0.0

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    balance: Optional[float] = None

# 履歴管理スキーマ
class TripCreate(BaseModel):
    user_id: int
    card_id: Optional[str] = None
    station_in: str
    gate_in: str
    status: Optional[str] = "in_progress"
    fare: Optional[float] = 0.0
    used_pass_id: Optional[int] = None

class TripUpdate(BaseModel):
    user_id: Optional[int] = None
    card_id: Optional[str] = None
    station_in: Optional[str] = None
    gate_in: Optional[str] = None
    station_out: Optional[str] = None
    gate_out: Optional[str] = None
    status: Optional[str] = None
    fare: Optional[float] = None
    used_pass_id: Optional[int] = None

# カード管理スキーマ
class CardCreate(BaseModel):
    user_id: Optional[int] = None
    idm: Optional[str] = None
    qr_token: Optional[str] = None
    label: Optional[str] = None

class CardUpdate(BaseModel):
    user_id: Optional[int] = None
    idm: Optional[str] = None
    qr_token: Optional[str] = None
    label: Optional[str] = None

class PurchaseRequest(BaseModel):
    scan_source: str
    card_idm: Optional[str] = None
    qr_token: Optional[str] = None
    amount: float
    description: str
    store_code: str
    device_id: str
    timestamp: Optional[datetime] = None

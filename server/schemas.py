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

class PurchaseRequest(BaseModel):
    scan_source: str
    card_idm: Optional[str] = None
    qr_token: Optional[str] = None
    amount: float
    description: str
    store_code: str
    device_id: str
    timestamp: Optional[datetime] = None

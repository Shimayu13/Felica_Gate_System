from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ScanRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scan_source: str  # "qr", "felica", or "face"
    card_idm: Optional[str] = None
    qr_token: Optional[str] = None
    face_image_base64: Optional[str] = None  # Base64エンコードされた顔画像（face認証時）
    station_code: str
    gate_code: str
    timestamp: datetime
    device_id: str

class ScanResponse(BaseModel):
    mode: str
    user_id: Optional[int] = None
    balance: Optional[float] = None
    usage_amount: Optional[float] = None

class ErrorResponse(BaseModel):
    status: str
    message: str

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
    pass_type: str  # "commuter" or "student"
    station_from: str
    station_to: str
    valid_from: datetime
    valid_until: datetime

class PassResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    pass_type: str
    station_from: str
    station_to: str
    valid_from: datetime
    valid_until: datetime
    is_active: int

class PurchaseRequest(BaseModel):
    scan_source: str  # "qr" or "felica"
    card_idm: Optional[str] = None
    qr_token: Optional[str] = None
    amount: float  # 購入金額
    description: Optional[str] = None  # 商品説明
    store_code: Optional[str] = None  # 店舗コード
    device_id: str
    timestamp: datetime

class FaceRegisterRequest(BaseModel):
    user_id: int
    face_image_base64: str  # Base64エンコードされた顔画像

class FaceVerifyRequest(BaseModel):
    face_image_base64: str  # Base64エンコードされた顔画像
    station_code: Optional[str] = None  # 改札で使用する場合
    gate_code: Optional[str] = None
    device_id: Optional[str] = None
    timestamp: Optional[datetime] = None

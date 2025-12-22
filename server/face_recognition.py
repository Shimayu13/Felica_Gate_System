"""
顔認証機能
DeepFaceを使用した顔登録・認証ロジック
"""

import base64
import json
import os
from io import BytesIO
from PIL import Image
from deepface import DeepFace
import numpy as np

# HEIC形式のサポートを有効化
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass  # pillow-heifがインストールされていない場合はスキップ

# 顔画像を一時保存するディレクトリ
FACE_TEMP_DIR = "face_temp"
os.makedirs(FACE_TEMP_DIR, exist_ok=True)

def base64_to_image(base64_string: str) -> str:
    """
    Base64文字列を画像ファイルに変換して保存

    Args:
        base64_string: Base64エンコードされた画像データ

    Returns:
        str: 保存された画像ファイルのパス
    """
    try:
        # Base64デコード
        image_data = base64.b64decode(base64_string)

        # PIL Imageとして開く
        image = Image.open(BytesIO(image_data))

        # 画像フォーマットを確認
        if image.format not in ['JPEG', 'PNG', 'JPG']:
            # サポートされていないフォーマットの場合、RGB変換してJPEGで保存
            if image.mode != 'RGB':
                image = image.convert('RGB')

        # 一時ファイルとして保存
        import uuid
        # 元の形式を保持（JPEGまたはPNG）
        ext = 'jpg' if image.format in ['JPEG', 'JPG'] or image.format is None else 'png'
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(FACE_TEMP_DIR, filename)

        # RGB変換が必要な場合
        if image.mode in ('RGBA', 'LA', 'P'):
            # アルファチャンネルがある場合はRGBに変換
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            rgb_image.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = rgb_image

        image.save(filepath, 'JPEG' if ext == 'jpg' else 'PNG')

        return filepath

    except Exception as e:
        raise ValueError(f"画像の変換に失敗しました: {str(e)}")

def extract_face_embedding(image_path: str) -> list:
    """
    顔画像から特徴量（エンベディング）を抽出

    Args:
        image_path: 画像ファイルのパス

    Returns:
        list: 顔の特徴量ベクトル

    Raises:
        ValueError: 顔が検出できない場合
    """
    try:
        # DeepFaceで顔の特徴量を抽出
        # モデル: VGG-Face (高精度), Facenet (高速), OpenFace, DeepFace, ArcFace
        embedding_objs = DeepFace.represent(
            img_path=image_path,
            model_name="Facenet",  # Facenetは高速で精度も良い
            enforce_detection=True,  # 顔が検出できない場合はエラー
            detector_backend="opencv"  # opencv, ssd, dlib, mtcnn, retinaface, mediapipe
        )

        if not embedding_objs or len(embedding_objs) == 0:
            raise ValueError("顔が検出できませんでした")

        # 最初の顔の特徴量を取得
        embedding = embedding_objs[0]["embedding"]

        return embedding

    except Exception as e:
        raise ValueError(f"顔の特徴量抽出に失敗: {str(e)}")

    finally:
        # 一時ファイルを削除
        if os.path.exists(image_path):
            os.remove(image_path)

def verify_faces(face_image_base64: str, stored_embedding: list, threshold: float = 0.4) -> dict:
    """
    顔画像と保存された特徴量を比較

    Args:
        face_image_base64: Base64エンコードされた顔画像
        stored_embedding: データベースに保存された顔の特徴量
        threshold: 類似度の閾値 (0.0-1.0, 低いほど厳しい)

    Returns:
        dict: {
            "verified": bool,  # 認証成功/失敗
            "distance": float,  # 距離（小さいほど似ている）
            "threshold": float,  # 使用した閾値
            "similarity": float  # 類似度（0-100%）
        }
    """
    # 入力画像から特徴量を抽出
    image_path = base64_to_image(face_image_base64)

    try:
        input_embedding = extract_face_embedding(image_path)

        # コサイン類似度を計算
        # DeepFaceはL2距離を使用するが、ここではコサイン類似度も計算
        input_np = np.array(input_embedding)
        stored_np = np.array(stored_embedding)

        # L2距離（ユークリッド距離）
        distance = np.linalg.norm(input_np - stored_np)

        # コサイン類似度
        cosine_similarity = np.dot(input_np, stored_np) / (
            np.linalg.norm(input_np) * np.linalg.norm(stored_np)
        )

        # 類似度をパーセンテージに変換
        similarity_percent = (1 - distance) * 100 if distance < 1 else 0

        # 認証判定 (Facenetの推奨閾値: 10.0前後、ここでは調整可能に)
        # 距離が小さいほど似ている
        verified = distance < threshold

        return {
            "verified": verified,
            "distance": float(distance),
            "threshold": threshold,
            "similarity": float(similarity_percent),
            "cosine_similarity": float(cosine_similarity)
        }

    except Exception as e:
        return {
            "verified": False,
            "distance": 999.0,
            "threshold": threshold,
            "similarity": 0.0,
            "error": str(e)
        }

def register_face(user_id: int, face_image_base64: str) -> dict:
    """
    顔を登録

    Args:
        user_id: ユーザーID
        face_image_base64: Base64エンコードされた顔画像

    Returns:
        dict: {
            "success": bool,
            "embedding": list,  # 特徴量ベクトル
            "message": str
        }
    """
    try:
        # 画像を保存
        image_path = base64_to_image(face_image_base64)

        # 特徴量を抽出
        embedding = extract_face_embedding(image_path)

        return {
            "success": True,
            "embedding": embedding,
            "message": "顔の登録に成功しました"
        }

    except Exception as e:
        return {
            "success": False,
            "embedding": None,
            "message": f"顔の登録に失敗: {str(e)}"
        }

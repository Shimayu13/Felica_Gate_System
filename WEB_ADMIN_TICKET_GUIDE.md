# Web管理画面 - 切符発券機能 実装ガイド

アカウント不要の切符発券機能をWeb管理画面に実装するためのガイドです。

## 概要

- Web管理画面で切符を発券
- 発券した切符のQRコードを表示・印刷
- iOS改札アプリでQRコードをスキャンして改札を通過
- 切符の種類: 片道、往復、一日券

## システム構成

```
┌─────────────────┐
│  Web管理画面    │ ← 駅員が操作
│  (切符発券)     │
└────────┬────────┘
         │ 切符発券
         ↓
┌─────────────────┐
│   サーバー      │
│  (FastAPI)      │
│   Database      │
└────────┬────────┘
         │ QRトークン
         ↓
┌─────────────────┐
│  印刷QRコード   │ ← 乗客に渡す
│  または画面表示 │
└────────┬────────┘
         │ スキャン
         ↓
┌─────────────────┐
│  iOS改札アプリ  │
│  (スキャン)     │
└─────────────────┘
```

## データベーススキーマ

### tickets テーブル

```sql
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id TEXT UNIQUE NOT NULL,
    qr_token TEXT UNIQUE NOT NULL,
    origin_station TEXT NOT NULL,
    destination_station TEXT NOT NULL,
    ticket_type TEXT NOT NULL,  -- 'single', 'round_trip', 'day_pass'
    price INTEGER NOT NULL,
    status TEXT DEFAULT 'active',  -- 'active', 'used', 'expired', 'cancelled'
    valid_until TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used_at TIMESTAMP,
    created_by TEXT,  -- 発券した駅員のID
    notes TEXT
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_tickets_qr_token ON tickets(qr_token);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON tickets(created_at);
```

### tickets_usage ログテーブル（オプション）

```sql
CREATE TABLE IF NOT EXISTS ticket_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id TEXT NOT NULL,
    qr_token TEXT NOT NULL,
    action TEXT NOT NULL,  -- 'entry', 'exit'
    station_code TEXT NOT NULL,
    gate_code TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
);
```

## サーバー側API実装

### 1. 切符発券API

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import secrets

router = APIRouter()

class TicketIssueRequest(BaseModel):
    origin_station: str
    destination_station: str
    ticket_type: str  # "single", "round_trip", "day_pass"
    issued_by: str  # 駅員ID
    notes: str | None = None

class IssuedTicket(BaseModel):
    ticket_id: str
    qr_token: str
    origin_station: str
    destination_station: str
    ticket_type: str
    price: int
    valid_until: str
    created_at: str

# 料金計算
def calculate_price(origin: str, destination: str, ticket_type: str) -> int:
    # 基本料金テーブル（実際は駅間の距離に基づいて計算）
    base_prices = {
        ("STATION_1", "STATION_2"): 200,
        ("STATION_1", "STATION_3"): 300,
        ("STATION_1", "STATION_4"): 400,
        ("STATION_1", "STATION_5"): 500,
        ("STATION_2", "STATION_3"): 200,
        ("STATION_2", "STATION_4"): 300,
        ("STATION_2", "STATION_5"): 400,
        ("STATION_3", "STATION_4"): 200,
        ("STATION_3", "STATION_5"): 300,
        ("STATION_4", "STATION_5"): 200,
    }

    # 往復の場合は逆方向も考慮
    base_price = base_prices.get((origin, destination)) or \
                 base_prices.get((destination, origin), 200)

    if ticket_type == "round_trip":
        return base_price * 2
    elif ticket_type == "day_pass":
        return 1000  # 一日券は固定料金
    else:  # single
        return base_price

# QRトークン生成（推測不可能）
def generate_qr_token() -> str:
    random_str = secrets.token_urlsafe(24)
    return f"TICKET_QR_{random_str}"

# 切符ID生成
def generate_ticket_id() -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = secrets.token_hex(3)
    return f"TKT{timestamp}{random_suffix.upper()}"

@router.post("/admin/ticket/issue")
async def issue_ticket(request: TicketIssueRequest) -> IssuedTicket:
    """
    Web管理画面から切符を発券
    """

    # バリデーション
    valid_stations = ["STATION_1", "STATION_2", "STATION_3", "STATION_4", "STATION_5"]
    if request.origin_station not in valid_stations:
        raise HTTPException(status_code=400, detail="Invalid origin station")
    if request.destination_station not in valid_stations:
        raise HTTPException(status_code=400, detail="Invalid destination station")
    if request.origin_station == request.destination_station:
        raise HTTPException(status_code=400, detail="Origin and destination must be different")

    valid_ticket_types = ["single", "round_trip", "day_pass"]
    if request.ticket_type not in valid_ticket_types:
        raise HTTPException(status_code=400, detail="Invalid ticket type")

    # 切符情報を生成
    ticket_id = generate_ticket_id()
    qr_token = generate_qr_token()
    price = calculate_price(request.origin_station, request.destination_station, request.ticket_type)

    # 有効期限を設定
    now = datetime.now()
    if request.ticket_type == "day_pass":
        # 一日券：当日23:59:59まで
        valid_until = now.replace(hour=23, minute=59, second=59, microsecond=0)
    else:
        # 片道・往復：購入から24時間
        valid_until = now + timedelta(hours=24)

    # データベースに保存
    cursor.execute(
        """
        INSERT INTO tickets
        (ticket_id, qr_token, origin_station, destination_station,
         ticket_type, price, status, valid_until, created_by, notes)
        VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
        """,
        (ticket_id, qr_token, request.origin_station, request.destination_station,
         request.ticket_type, price, valid_until.isoformat(),
         request.issued_by, request.notes)
    )
    conn.commit()

    print(f"✅ 切符発券: {ticket_id} (QR: {qr_token[:20]}...)")

    # レスポンスを返す
    return IssuedTicket(
        ticket_id=ticket_id,
        qr_token=qr_token,
        origin_station=request.origin_station,
        destination_station=request.destination_station,
        ticket_type=request.ticket_type,
        price=price,
        valid_until=valid_until.isoformat() + "Z",
        created_at=now.isoformat() + "Z"
    )

@router.get("/admin/ticket/{ticket_id}")
async def get_ticket(ticket_id: str):
    """
    切符情報を取得（再印刷用）
    """
    cursor.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,))
    ticket = cursor.fetchone()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return ticket

@router.get("/admin/tickets")
async def list_tickets(
    status: str | None = None,
    limit: int = 50,
    offset: int = 0
):
    """
    切符一覧を取得
    """
    query = "SELECT * FROM tickets"
    params = []

    if status:
        query += " WHERE status = ?"
        params.append(status)

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, params)
    tickets = cursor.fetchall()

    return {"tickets": tickets, "count": len(tickets)}
```

### 2. 改札スキャンAPIの修正

```python
@router.post("/scan")
async def scan(request: ScanRequest):
    """
    改札スキャン（切符QRトークン対応版）
    """

    if request.qr_token and request.qr_token.startswith("TICKET_QR_"):
        # 切符でのスキャン
        return await handle_ticket_scan(request)
    elif request.qr_token:
        # 通常のユーザーQRトークン
        return await handle_user_scan(request)
    elif request.card_idm:
        # FeliCaカード
        return await handle_felica_scan(request)
    elif request.face_image_base64:
        # 顔認証
        return await handle_face_scan(request)
    else:
        raise HTTPException(400, "No valid authentication method")

async def handle_ticket_scan(request: ScanRequest):
    """切符でのスキャン処理"""

    # 切符情報を取得
    cursor.execute(
        "SELECT * FROM tickets WHERE qr_token = ?",
        (request.qr_token,)
    )
    ticket = cursor.fetchone()

    if not ticket:
        raise HTTPException(404, "Ticket not found")

    # ステータスチェック
    if ticket['status'] == 'used':
        raise HTTPException(400, "Ticket already used")
    if ticket['status'] == 'expired':
        raise HTTPException(400, "Ticket has expired")
    if ticket['status'] == 'cancelled':
        raise HTTPException(400, "Ticket has been cancelled")

    # 有効期限チェック
    valid_until = datetime.fromisoformat(ticket['valid_until'].replace('Z', ''))
    if datetime.now() > valid_until:
        cursor.execute(
            "UPDATE tickets SET status = 'expired' WHERE qr_token = ?",
            (request.qr_token,)
        )
        conn.commit()
        raise HTTPException(400, "Ticket has expired")

    # 入場/出場の判定
    cursor.execute(
        """
        SELECT * FROM ticket_usage
        WHERE qr_token = ?
        ORDER BY timestamp DESC LIMIT 1
        """,
        (request.qr_token,)
    )
    last_usage = cursor.fetchone()

    if last_usage is None or last_usage['action'] == 'exit':
        mode = 'entry'
    else:
        mode = 'exit'

        # 片道切符の場合は使用済みにする
        if ticket['ticket_type'] == 'single':
            cursor.execute(
                "UPDATE tickets SET status = 'used', used_at = ? WHERE qr_token = ?",
                (datetime.now().isoformat(), request.qr_token)
            )

    # 使用ログを記録
    cursor.execute(
        """
        INSERT INTO ticket_usage
        (ticket_id, qr_token, action, station_code, gate_code)
        VALUES (?, ?, ?, ?, ?)
        """,
        (ticket['ticket_id'], request.qr_token, mode,
         request.station_code, request.gate_code)
    )

    # ゲートログも記録
    cursor.execute(
        """
        INSERT INTO gate_logs
        (scan_source, qr_token, station_code, gate_code,
         timestamp, device_id, mode)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        ('qr', request.qr_token, request.station_code, request.gate_code,
         request.timestamp, request.device_id, mode)
    )

    conn.commit()

    return {
        "success": True,
        "mode": mode,
        "message": f"切符による{'入場' if mode == 'entry' else '出場'}完了",
        "user_name": "ゲスト（切符）",
        "ticket_id": ticket['ticket_id'],
        "ticket_type": ticket['ticket_type'],
        "origin": ticket['origin_station'],
        "destination": ticket['destination_station'],
        "valid_until": ticket['valid_until']
    }
```

## Web管理画面の実装

### HTML/JavaScript例

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>切符発券システム</title>
    <script src="https://cdn.jsdelivr.net/npm/qrcode@1.5.3/build/qrcode.min.js"></script>
    <style>
        .ticket-form {
            max-width: 600px;
            margin: 20px auto;
            padding: 20px;
            border: 1px solid #ccc;
            border-radius: 8px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        select, input, button {
            width: 100%;
            padding: 8px;
            font-size: 16px;
        }
        button {
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
            margin-top: 10px;
        }
        button:hover {
            background-color: #45a049;
        }
        #ticketDisplay {
            max-width: 600px;
            margin: 20px auto;
            padding: 20px;
            border: 2px solid #4CAF50;
            border-radius: 8px;
            display: none;
            text-align: center;
        }
        #qrcode {
            margin: 20px auto;
        }
        .print-button {
            background-color: #2196F3;
        }
    </style>
</head>
<body>
    <h1 style="text-align: center;">切符発券システム</h1>

    <!-- 発券フォーム -->
    <div class="ticket-form">
        <h2>新規切符発券</h2>

        <div class="form-group">
            <label>出発駅:</label>
            <select id="originStation">
                <option value="STATION_1">STATION_1</option>
                <option value="STATION_2">STATION_2</option>
                <option value="STATION_3">STATION_3</option>
                <option value="STATION_4">STATION_4</option>
                <option value="STATION_5">STATION_5</option>
            </select>
        </div>

        <div class="form-group">
            <label>到着駅:</label>
            <select id="destStation">
                <option value="STATION_2">STATION_2</option>
                <option value="STATION_3">STATION_3</option>
                <option value="STATION_4">STATION_4</option>
                <option value="STATION_5">STATION_5</option>
            </select>
        </div>

        <div class="form-group">
            <label>切符種類:</label>
            <select id="ticketType">
                <option value="single">片道切符</option>
                <option value="round_trip">往復切符</option>
                <option value="day_pass">一日券</option>
            </select>
        </div>

        <div class="form-group">
            <label>駅員ID:</label>
            <input type="text" id="staffId" placeholder="例: STAFF001">
        </div>

        <div class="form-group">
            <label>備考（オプション）:</label>
            <input type="text" id="notes" placeholder="特記事項があれば入力">
        </div>

        <button onclick="issueTicket()">切符を発券</button>
    </div>

    <!-- 発券済み切符表示 -->
    <div id="ticketDisplay">
        <h2>発券完了</h2>
        <p><strong>切符ID:</strong> <span id="ticketId"></span></p>
        <p><strong>種類:</strong> <span id="displayType"></span></p>
        <p><strong>区間:</strong> <span id="displayRoute"></span></p>
        <p><strong>料金:</strong> ¥<span id="displayPrice"></span></p>
        <p><strong>有効期限:</strong> <span id="displayValidUntil"></span></p>

        <div id="qrcode"></div>

        <button class="print-button" onclick="window.print()">印刷</button>
        <button onclick="resetForm()">新しい切符を発券</button>
    </div>

    <script>
        const API_BASE = 'http://localhost:8000';

        async function issueTicket() {
            const origin = document.getElementById('originStation').value;
            const dest = document.getElementById('destStation').value;
            const type = document.getElementById('ticketType').value;
            const staffId = document.getElementById('staffId').value;
            const notes = document.getElementById('notes').value;

            if (!staffId) {
                alert('駅員IDを入力してください');
                return;
            }

            const request = {
                origin_station: origin,
                destination_station: dest,
                ticket_type: type,
                issued_by: staffId,
                notes: notes || null
            };

            try {
                const response = await fetch(`${API_BASE}/admin/ticket/issue`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(request)
                });

                if (!response.ok) {
                    throw new Error('発券に失敗しました');
                }

                const ticket = await response.json();
                displayTicket(ticket);

            } catch (error) {
                alert('エラー: ' + error.message);
            }
        }

        function displayTicket(ticket) {
            // フォームを隠す
            document.querySelector('.ticket-form').style.display = 'none';

            // 切符情報を表示
            document.getElementById('ticketId').textContent = ticket.ticket_id;
            document.getElementById('displayType').textContent = getTicketTypeName(ticket.ticket_type);
            document.getElementById('displayRoute').textContent =
                `${ticket.origin_station} → ${ticket.destination_station}`;
            document.getElementById('displayPrice').textContent = ticket.price;
            document.getElementById('displayValidUntil').textContent =
                new Date(ticket.valid_until).toLocaleString('ja-JP');

            // QRコードを生成
            document.getElementById('qrcode').innerHTML = '';
            new QRCode(document.getElementById('qrcode'), {
                text: ticket.qr_token,
                width: 256,
                height: 256
            });

            // 切符表示エリアを表示
            document.getElementById('ticketDisplay').style.display = 'block';
        }

        function getTicketTypeName(type) {
            const names = {
                'single': '片道切符',
                'round_trip': '往復切符',
                'day_pass': '一日券'
            };
            return names[type] || type;
        }

        function resetForm() {
            document.querySelector('.ticket-form').style.display = 'block';
            document.getElementById('ticketDisplay').style.display = 'none';
            document.getElementById('notes').value = '';
        }
    </script>
</body>
</html>
```

## 運用フロー

1. **切符発券**
   - 駅員がWeb管理画面で切符を発券
   - 出発駅、到着駅、切符種類を選択
   - QRコードが生成・表示される
   - QRコードを印刷または画面表示で乗客に渡す

2. **改札通過**
   - 乗客が改札でQRコードをスキャン
   - iOS改札アプリが `/scan` APIを呼び出し
   - サーバーが切符の有効性を確認
   - 入場または出場を記録

3. **切符管理**
   - 使用済み切符の確認
   - 有効期限切れ切符の自動更新
   - 切符の再発行（紛失時など）

## まとめ

- iOS側から切符購入機能を削除 ✅
- Web管理画面で切符発券
- 発券したQRコードをiOS改札アプリでスキャン
- データベースに切符情報と使用ログを記録

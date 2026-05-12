const API_ROOT = 'http://127.0.0.1:8000'

async function fetchUsers() {
  const res = await fetch(`${API_ROOT}/users`)
  return res.json()
}

async function fetchCards() {
  const res = await fetch(`${API_ROOT}/cards`)
  return res.json()
}

async function refreshCards() {
  const cards = await fetchCards()
  renderCards(cards)
}

function renderUsers(users) {
  const container = document.getElementById('users')
  container.innerHTML = ''

  if (users.length === 0) {
    container.innerHTML = '<p class="empty-state">ユーザーが見つかりません</p>'
    return
  }

  users.forEach(u => {
    const el = document.createElement('div')
    el.className = 'user'
    el.innerHTML = `
      <div>
        <strong>${u.name}</strong>
        <div class="user-info">ID: ${u.id} ${u.email ? `| ${u.email}` : ''}</div>
      </div>
      <div class="balance">¥${parseFloat(u.balance || 0).toLocaleString()}</div>
      <div class="user-actions">
        <button onclick="adjustBalance(${u.id})" class="btn btn-secondary">残高調整</button>
        <button onclick="editUser(${u.id})" class="btn btn-info">編集</button>
        <button onclick="deleteUser(${u.id})" class="btn btn-danger">削除</button>
      </div>
    `
    container.appendChild(el)
  })
}

function renderTrips(trips) {
  const container = document.getElementById('trips')
  container.innerHTML = ''

  if (trips.length === 0) {
    container.innerHTML = '<p class="empty-state">履歴が見つかりません</p>'
    return
  }

  trips.forEach(t => {
    const el = document.createElement('div')
    el.className = 'trip'

    const statusClass = t.status === 'in_progress' ? 'status-in_progress' :
                       t.status === 'completed' ? 'status-completed' : 'status-cancelled'

    const passInfo = t.used_pass_id ? `<div class="pass-info">🚫 パス使用: ${t.used_pass_id}</div>` : ''

    const actionButtons = t.status === 'in_progress' 
      ? `<button onclick="cancelTrip(${t.id})" class="btn btn-warning">キャンセル</button>`
      : `<button onclick="editTrip(${t.id})" class="btn btn-info">編集</button>`

    el.innerHTML = `
      <div class="trip-id">#${t.id}</div>
      <div class="trip-details">
        <div><strong>ユーザー:</strong> ${t.user_name || '不明'}</div>
        <div><strong>駅:</strong> ${t.station_name || '不明'}</div>
        <div><strong>料金:</strong> ¥${parseFloat(t.fare || 0).toLocaleString()}</div>
        <div><strong>時刻:</strong> ${new Date(t.timestamp).toLocaleString('ja-JP')}</div>
      </div>
      <div class="trip-route">${t.entry_station || '不明'} → ${t.exit_station || '不明'}</div>
      <span class="trip-status ${statusClass}">${t.status}</span>
      ${passInfo}
      <div class="trip-actions">
        ${actionButtons}
        <button onclick="deleteTrip(${t.id})" class="btn btn-danger">削除</button>
      </div>
    `
    container.appendChild(el)
  })
}

async function refreshUsers() {
  const users = await fetchUsers()
  renderUsers(users)
}

async function refreshTrips() {
  const trips = await fetchTrips()
  renderTrips(trips)
}

function renderCards(cards) {
  const container = document.getElementById('cards')
  container.innerHTML = ''

  if (cards.length === 0) {
    container.innerHTML = '<p class="empty-state">カードが見つかりません</p>'
    return
  }

  cards.forEach(c => {
    const el = document.createElement('div')
    el.className = 'card-item'
    el.innerHTML = `
      <div class="card-info">
        <div><strong>ID:</strong> ${c.id}</div>
        <div><strong>ユーザー:</strong> ${c.user_id ? `ID ${c.user_id}` : '未割り当て'}</div>
        <div><strong>Felica ID:</strong> ${c.idm || '未設定'}</div>
        <div><strong>QRトークン:</strong> ${c.qr_token || '未設定'}</div>
        <div><strong>ラベル:</strong> ${c.label || '未設定'}</div>
      </div>
      <div class="card-actions">
        <button onclick="editCard(${c.id})" class="btn btn-info">編集</button>
        <button onclick="deleteCard(${c.id})" class="btn btn-danger">削除</button>
      </div>
    `
    container.appendChild(el)
  })
}

async function adjustBalance(userId) {
  const v = prompt('New balance:')
  if (v === null) return
  const amount = parseFloat(v)
  await fetch(`${API_ROOT}/users/${userId}/balance?amount=${amount}`, { method: 'PATCH' })
  refreshUsers()
}

async function cancelTrip(id) {
  await fetch(`${API_ROOT}/trips/${id}/cancel`, { method: 'PATCH' })
  refreshTrips()
}

// ユーザー管理機能
async function createUser() {
  const name = prompt('ユーザー名:')
  if (!name) return
  
  const email = prompt('メールアドレス (オプション):')
  const balance = parseFloat(prompt('初期残高 (¥):') || '0')
  
  try {
    await fetch(`${API_ROOT}/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email: email || null, balance })
    })
    refreshUsers()
  } catch (e) {
    alert('ユーザー作成に失敗しました')
  }
}

async function editUser(userId) {
  const user = await fetch(`${API_ROOT}/users/${userId}`).then(r => r.json())
  
  const name = prompt('ユーザー名:', user.name)
  if (!name) return
  
  const email = prompt('メールアドレス:', user.email || '')
  const balance = parseFloat(prompt('残高 (¥):', user.balance) || '0')
  
  try {
    await fetch(`${API_ROOT}/users/${userId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email: email || null, balance })
    })
    refreshUsers()
  } catch (e) {
    alert('ユーザー更新に失敗しました')
  }
}

async function deleteUser(userId) {
  if (!confirm('このユーザーを削除しますか？')) return
  
  try {
    await fetch(`${API_ROOT}/users/${userId}`, { method: 'DELETE' })
    refreshUsers()
  } catch (e) {
    alert('ユーザー削除に失敗しました')
  }
}

// 履歴管理機能
async function createTrip() {
  const userId = parseInt(prompt('ユーザーID:'))
  if (!userId) return
  
  const stationIn = prompt('入場駅:')
  if (!stationIn) return
  
  const gateIn = prompt('入場ゲート:')
  const fare = parseFloat(prompt('料金 (¥):') || '0')
  
  try {
    await fetch(`${API_ROOT}/trips`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, station_in: stationIn, gate_in: gateIn, fare })
    })
    refreshTrips()
  } catch (e) {
    alert('履歴作成に失敗しました')
  }
}

async function editTrip(tripId) {
  const trip = await fetch(`${API_ROOT}/trips/${tripId}`).then(r => r.json())
  
  const userId = parseInt(prompt('ユーザーID:', trip.user_id))
  if (!userId) return
  
  const stationIn = prompt('入場駅:', trip.station_in)
  if (!stationIn) return
  
  const gateIn = prompt('入場ゲート:', trip.gate_in)
  const stationOut = prompt('出場駅:', trip.station_out || '')
  const gateOut = prompt('出場ゲート:', trip.gate_out || '')
  const fare = parseFloat(prompt('料金 (¥):', trip.fare) || '0')
  const status = prompt('ステータス (in_progress/completed/cancelled):', trip.status)
  
  try {
    await fetch(`${API_ROOT}/trips/${tripId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        user_id: userId, 
        station_in: stationIn, 
        gate_in: gateIn,
        station_out: stationOut || null,
        gate_out: gateOut || null,
        fare,
        status
      })
    })
    refreshTrips()
  } catch (e) {
    alert('履歴更新に失敗しました')
  }
}

async function deleteTrip(tripId) {
  if (!confirm('この履歴を削除しますか？')) return
  
  try {
    await fetch(`${API_ROOT}/trips/${tripId}`, { method: 'DELETE' })
    refreshTrips()
  } catch (e) {
    alert('履歴削除に失敗しました')
  }
}

// カード管理機能
async function createCard() {
  const userId = prompt('ユーザーID (オプション):')
  const idm = prompt('Felica ID (オプション):')
  const qrToken = prompt('QRトークン (オプション):')
  const label = prompt('ラベル (オプション):')
  
  try {
    await fetch(`${API_ROOT}/cards`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        user_id: userId || null, 
        idm: idm || null, 
        qr_token: qrToken || null, 
        label: label || null 
      })
    })
    refreshCards()
  } catch (e) {
    alert('カード作成に失敗しました')
  }
}

async function editCard(cardId) {
  const card = await fetch(`${API_ROOT}/cards/${cardId}`).then(r => r.json())
  
  const userId = prompt('ユーザーID:', card.user_id || '')
  const idm = prompt('Felica ID:', card.idm || '')
  const qrToken = prompt('QRトークン:', card.qr_token || '')
  const label = prompt('ラベル:', card.label || '')
  
  try {
    await fetch(`${API_ROOT}/cards/${cardId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        user_id: userId || null, 
        idm: idm || null, 
        qr_token: qrToken || null, 
        label: label || null 
      })
    })
    refreshCards()
  } catch (e) {
    alert('カード更新に失敗しました')
  }
}

async function deleteCard(cardId) {
  if (!confirm('このカードを削除しますか？')) return
  
  try {
    await fetch(`${API_ROOT}/cards/${cardId}`, { method: 'DELETE' })
    refreshCards()
  } catch (e) {
    alert('カード削除に失敗しました')
  }
}

document.getElementById('refreshUsers').addEventListener('click', refreshUsers)
document.getElementById('refreshTrips').addEventListener('click', refreshTrips)
document.getElementById('createUser').addEventListener('click', createUser)
document.getElementById('createTrip').addEventListener('click', createTrip)
document.getElementById('refreshCards').addEventListener('click', refreshCards)
document.getElementById('createCard').addEventListener('click', createCard)

// initial load
refreshUsers();
refreshTrips();
refreshCards();

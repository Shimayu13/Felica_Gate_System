const API_ROOT = 'http://127.0.0.1:8001'

async function fetchUsers() {
  const res = await fetch(`${API_ROOT}/users`)
  return res.json()
}

async function fetchTrips() {
  const res = await fetch(`${API_ROOT}/trips`)
  return res.json()
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
      <button onclick="adjustBalance(${u.id})" class="btn btn-secondary">残高調整</button>
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
      ${t.status === 'in_progress' ? `<button onclick="cancelTrip(${t.id})">キャンセル</button>` : ''}
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

document.getElementById('refreshUsers').addEventListener('click', refreshUsers)
document.getElementById('refreshTrips').addEventListener('click', refreshTrips)

// initial load
refreshUsers();
refreshTrips();

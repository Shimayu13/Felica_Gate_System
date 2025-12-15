const API_ROOT = 'http://127.0.0.1:8000'

// ==================== モーダル管理 ====================
const modal = document.getElementById('modal')
const modalTitle = document.getElementById('modalTitle')
const modalBody = document.getElementById('modalBody')
const closeBtn = document.querySelector('.close')

function showModal(title, content) {
  modalTitle.textContent = title
  modalBody.innerHTML = content
  modal.classList.add('show')
}

function hideModal() {
  modal.classList.remove('show')
}

closeBtn.addEventListener('click', hideModal)
window.addEventListener('click', (e) => {
  if (e.target === modal) {
    hideModal()
  }
})

// ==================== API呼び出し ====================
async function fetchUsers() {
  const res = await fetch(`${API_ROOT}/users`)
  return res.json()
}

async function fetchPasses(activeOnly = false) {
  const url = activeOnly ? `${API_ROOT}/passes?active_only=true` : `${API_ROOT}/passes`
  const res = await fetch(url)
  return res.json()
}

async function fetchTrips(status = '') {
  // 全件取得するためにlimitを大きく設定
  const url = status ? `${API_ROOT}/trips?status=${status}&limit=10000` : `${API_ROOT}/trips?limit=10000`
  const res = await fetch(url)
  return res.json()
}

async function fetchStations() {
  const res = await fetch(`${API_ROOT}/stations`)
  return res.json()
}

async function fetchGates() {
  const res = await fetch(`${API_ROOT}/gates`)
  return res.json()
}

async function fetchCards() {
  const res = await fetch(`${API_ROOT}/cards`)
  return res.json()
}

// ==================== レンダリング ====================
function renderUsers(users) {
  const tbody = document.getElementById('users')
  tbody.innerHTML = ''

  if (users.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center">ユーザーがいません</td></tr>'
    return
  }

  users.forEach(u => {
    const balance = parseFloat(u.balance)
    const balanceClass = balance < 1000 ? 'badge-danger' : 'badge-success'
    const tr = document.createElement('tr')
    tr.innerHTML = `
      <td>${u.id}</td>
      <td><strong>${u.name}</strong></td>
      <td>${u.email || '-'}</td>
      <td><span class="badge ${balanceClass}">¥${balance.toLocaleString()}</span></td>
      <td><code>${u.qr_token || '-'}</code></td>
      <td>
        <button class="btn-warning btn-small" onclick="editBalance(${u.id}, ${balance}, '${u.name}')">残高編集</button>
        <button class="btn-danger btn-small" onclick="deleteUser(${u.id}, '${u.name}')">削除</button>
      </td>
    `
    tbody.appendChild(tr)
  })
}

function renderPasses(passes) {
  const tbody = document.getElementById('passes')
  tbody.innerHTML = ''

  const activeOnly = document.getElementById('filterActivePasses').checked
  const filtered = activeOnly ? passes.filter(p => p.is_active === 1) : passes

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="text-center">定期券がありません</td></tr>'
    return
  }

  filtered.forEach(p => {
    const validFrom = new Date(p.valid_from).toLocaleDateString('ja-JP')
    const validUntil = new Date(p.valid_until).toLocaleDateString('ja-JP')
    const now = new Date()
    const isValid = p.is_active === 1 && new Date(p.valid_until) > now
    const statusClass = isValid ? 'badge-success' : 'badge-secondary'
    const statusText = isValid ? '有効' : '無効'
    const passTypeName = p.pass_type === 'commuter' ? '通勤定期' : '通学定期'

    const tr = document.createElement('tr')
    tr.innerHTML = `
      <td>${p.id}</td>
      <td>${p.user_id}</td>
      <td>${passTypeName}</td>
      <td>${p.station_from} ⇄ ${p.station_to}</td>
      <td>${validFrom} ~ ${validUntil}</td>
      <td><span class="badge ${statusClass}">${statusText}</span></td>
      <td>
        ${isValid ? `<button class="btn-warning btn-small" onclick="deactivatePass(${p.id})">無効化</button>` : ''}
        <button class="btn-danger btn-small" onclick="deletePass(${p.id})">削除</button>
      </td>
    `
    tbody.appendChild(tr)
  })
}

let currentTripPage = 1
let allTrips = []

function renderTrips(trips) {
  allTrips = trips
  const tbody = document.getElementById('trips')
  tbody.innerHTML = ''

  const statusFilter = document.getElementById('tripStatusFilter').value
  const limit = parseInt(document.getElementById('tripLimitFilter').value)

  // フィルター適用
  let filtered = statusFilter ? trips.filter(t => t.status === statusFilter) : trips

  // 新しい順にソート
  filtered.sort((a, b) => new Date(b.entered_at) - new Date(a.entered_at))

  if (filtered.length === 0) {
    tbody.innerHTML = '<tr><td colspan="9" class="text-center">記録がありません</td></tr>'
    document.getElementById('tripPagination').innerHTML = ''
    return
  }

  // ページネーション計算
  let paginatedTrips
  let totalPages

  if (limit >= 999999) {
    // 「全て」が選択された場合はページネーションなし
    paginatedTrips = filtered
    totalPages = 1
  } else {
    totalPages = Math.ceil(filtered.length / limit)
    const startIndex = (currentTripPage - 1) * limit
    const endIndex = Math.min(startIndex + limit, filtered.length)
    paginatedTrips = filtered.slice(startIndex, endIndex)
  }

  paginatedTrips.forEach(t => {
    const enteredAt = new Date(t.entered_at).toLocaleString('ja-JP')
    const exitedAt = t.exited_at ? new Date(t.exited_at).toLocaleString('ja-JP') : '-'
    const statusClass = `status-${t.status}`
    const statusTextMap = {
      'in_progress': '入場中',
      'completed': '完了',
      'cancelled': 'キャンセル'
    }
    const statusText = statusTextMap[t.status] || t.status

    // 支払方法の判定
    let paymentMethod = '-'
    let paymentClass = 'badge-secondary'
    if (t.status === 'completed') {
      if (t.used_pass_id) {
        paymentMethod = '定期券'
        paymentClass = 'badge-success'
      } else {
        paymentMethod = '残高'
        paymentClass = 'badge-info'
      }
    }

    // 運賃表示
    let fareDisplay = '-'
    if (t.status === 'completed') {
      if (t.fare_amount !== null && t.fare_amount !== undefined) {
        fareDisplay = `¥${parseFloat(t.fare_amount).toLocaleString()}`
      } else if (t.used_pass_id) {
        fareDisplay = '¥0'
      }
    }

    // 残高推移表示
    let balanceDisplay = '-'
    if (t.status === 'completed' && t.balance_before !== null && t.balance_before !== undefined) {
      const before = parseFloat(t.balance_before)
      const after = parseFloat(t.balance_after)
      const diff = after - before
      const arrow = diff < 0 ? '↓' : diff > 0 ? '↑' : '→'
      const diffColor = diff < 0 ? 'color: #d32f2f' : diff > 0 ? 'color: #2e7d32' : ''
      balanceDisplay = `
        <small>¥${before.toLocaleString()}</small><br>
        <span style="${diffColor}"><strong>${arrow} ¥${after.toLocaleString()}</strong></span>
      `
    }

    const tr = document.createElement('tr')
    tr.innerHTML = `
      <td>${t.id}</td>
      <td>${t.user_id || '-'}</td>
      <td>${t.station_in} (${t.gate_in})<br><small>${enteredAt}</small></td>
      <td>${t.station_out || '-'} ${t.gate_out ? '(' + t.gate_out + ')' : ''}<br><small>${exitedAt}</small></td>
      <td><span class="badge ${paymentClass}">${paymentMethod}</span></td>
      <td><strong>${fareDisplay}</strong></td>
      <td>${balanceDisplay}</td>
      <td><span class="${statusClass}">${statusText}</span></td>
      <td>
        ${t.status === 'in_progress' ? `<button class="btn-warning btn-small" onclick="showExitForm(${t.id})">出場登録</button>` : ''}
        ${t.status === 'in_progress' || t.status === 'completed' ? `<button class="btn-danger btn-small" onclick="cancelTrip(${t.id})">キャンセル</button>` : ''}
      </td>
    `
    tbody.appendChild(tr)
  })

  // ページネーション表示
  renderTripPagination(filtered.length, limit, totalPages)
}

function renderTripPagination(totalCount, limit, totalPages) {
  const pagination = document.getElementById('tripPagination')

  // 「全て」が選択されている場合は件数だけ表示
  if (limit >= 999999) {
    pagination.innerHTML = `<span class="pagination-info">全${totalCount}件を表示中</span>`
    return
  }

  if (totalPages <= 1) {
    pagination.innerHTML = ''
    return
  }

  let html = ''

  // 前へボタン
  html += `<button class="btn-secondary btn-small" onclick="changeTripPage(${currentTripPage - 1})" ${currentTripPage === 1 ? 'disabled' : ''}>« 前へ</button>`

  // ページ番号ボタン
  const maxButtons = 5
  let startPage = Math.max(1, currentTripPage - Math.floor(maxButtons / 2))
  let endPage = Math.min(totalPages, startPage + maxButtons - 1)

  if (endPage - startPage < maxButtons - 1) {
    startPage = Math.max(1, endPage - maxButtons + 1)
  }

  if (startPage > 1) {
    html += `<button class="btn-secondary btn-small" onclick="changeTripPage(1)">1</button>`
    if (startPage > 2) {
      html += `<span class="pagination-info">...</span>`
    }
  }

  for (let i = startPage; i <= endPage; i++) {
    const activeClass = i === currentTripPage ? 'active' : ''
    html += `<button class="btn-secondary btn-small ${activeClass}" onclick="changeTripPage(${i})">${i}</button>`
  }

  if (endPage < totalPages) {
    if (endPage < totalPages - 1) {
      html += `<span class="pagination-info">...</span>`
    }
    html += `<button class="btn-secondary btn-small" onclick="changeTripPage(${totalPages})">${totalPages}</button>`
  }

  // 次へボタン
  html += `<button class="btn-secondary btn-small" onclick="changeTripPage(${currentTripPage + 1})" ${currentTripPage === totalPages ? 'disabled' : ''}>次へ »</button>`

  // 情報表示
  const startIndex = (currentTripPage - 1) * limit + 1
  const endIndex = Math.min(currentTripPage * limit, totalCount)
  html += `<span class="pagination-info">${startIndex}-${endIndex} / ${totalCount}件</span>`

  pagination.innerHTML = html
}

function changeTripPage(page) {
  const limit = parseInt(document.getElementById('tripLimitFilter').value)
  const statusFilter = document.getElementById('tripStatusFilter').value

  // フィルター適用後のデータ数で計算
  let filtered = statusFilter ? allTrips.filter(t => t.status === statusFilter) : allTrips
  const totalPages = Math.ceil(filtered.length / limit)

  if (page < 1 || page > totalPages) return

  currentTripPage = page
  renderTrips(allTrips)
}

function renderStations(stations) {
  const tbody = document.getElementById('stations')
  tbody.innerHTML = ''

  if (stations.length === 0) {
    tbody.innerHTML = '<tr><td colspan="3" class="text-center">駅がありません</td></tr>'
    return
  }

  stations.forEach(s => {
    const tr = document.createElement('tr')
    tr.innerHTML = `
      <td>${s.id}</td>
      <td><code>${s.code}</code></td>
      <td>${s.name || s.code}</td>
    `
    tbody.appendChild(tr)
  })
}

function renderGates(gates) {
  const tbody = document.getElementById('gates')
  tbody.innerHTML = ''

  if (gates.length === 0) {
    tbody.innerHTML = '<tr><td colspan="4" class="text-center">ゲートがありません</td></tr>'
    return
  }

  gates.forEach(g => {
    const tr = document.createElement('tr')
    tr.innerHTML = `
      <td>${g.id}</td>
      <td><code>${g.code}</code></td>
      <td>${g.station_id}</td>
      <td>${g.name || g.code}</td>
    `
    tbody.appendChild(tr)
  })
}

function renderCards(cards) {
  const tbody = document.getElementById('cards')
  tbody.innerHTML = ''

  if (cards.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-center">カードがありません</td></tr>'
    return
  }

  cards.forEach(c => {
    const type = c.qr_token ? 'QR' : c.idm ? 'FeliCa' : '不明'
    const identifier = c.qr_token || c.idm || '-'
    const tr = document.createElement('tr')
    tr.innerHTML = `
      <td>${c.id}</td>
      <td>${c.user_id || '-'}</td>
      <td><span class="badge ${type === 'QR' ? 'badge-info' : 'badge-warning'}">${type}</span></td>
      <td><code>${identifier}</code></td>
      <td>${c.label || '-'}</td>
    `
    tbody.appendChild(tr)
  })
}

// ==================== リフレッシュ ====================
async function refreshUsers() {
  try {
    const users = await fetchUsers()
    renderUsers(users)
  } catch (error) {
    console.error('ユーザー取得エラー:', error)
    alert('ユーザー情報の取得に失敗しました')
  }
}

async function refreshPasses() {
  try {
    const passes = await fetchPasses()
    renderPasses(passes)
  } catch (error) {
    console.error('定期券取得エラー:', error)
    alert('定期券情報の取得に失敗しました')
  }
}

async function refreshTrips() {
  try {
    const trips = await fetchTrips()
    renderTrips(trips)
  } catch (error) {
    console.error('トリップ取得エラー:', error)
    alert('トリップ情報の取得に失敗しました')
  }
}

async function refreshStations() {
  try {
    const [stations, gates] = await Promise.all([fetchStations(), fetchGates()])
    renderStations(stations)
    renderGates(gates)
  } catch (error) {
    console.error('駅情報取得エラー:', error)
    alert('駅情報の取得に失敗しました')
  }
}

async function refreshCards() {
  try {
    const cards = await fetchCards()
    renderCards(cards)
  } catch (error) {
    console.error('カード取得エラー:', error)
    alert('カード情報の取得に失敗しました')
  }
}

async function refreshAll() {
  await Promise.all([
    refreshUsers(),
    refreshPasses(),
    refreshTrips(),
    refreshStations(),
    refreshCards()
  ])
}

// ==================== ユーザー操作 ====================
function showAddUserForm() {
  const content = `
    <form id="addUserForm">
      <div class="form-group">
        <label>名前 *</label>
        <input type="text" id="userName" required>
      </div>
      <div class="form-group">
        <label>メールアドレス</label>
        <input type="email" id="userEmail">
      </div>
      <div class="form-group">
        <label>初期残高 (円)</label>
        <input type="number" id="userBalance" value="10000" min="0" step="100">
      </div>
      <div class="form-group">
        <label>QRトークン</label>
        <input type="text" id="userQR" placeholder="例: QR_USER_001">
      </div>
      <div class="form-actions">
        <button type="button" class="btn-secondary" onclick="hideModal()">キャンセル</button>
        <button type="submit" class="btn-success">作成</button>
      </div>
    </form>
  `
  showModal('➕ ユーザー追加', content)

  document.getElementById('addUserForm').addEventListener('submit', async (e) => {
    e.preventDefault()
    const name = document.getElementById('userName').value
    const email = document.getElementById('userEmail').value
    const balance = parseFloat(document.getElementById('userBalance').value)
    const qr_token = document.getElementById('userQR').value

    try {
      const res = await fetch(`${API_ROOT}/users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, balance, qr_token })
      })
      const data = await res.json()
      if (res.ok) {
        hideModal()
        refreshUsers()
        alert('ユーザーを追加しました')
      } else {
        alert('エラー: ' + (data.message || data.detail))
      }
    } catch (error) {
      console.error(error)
      alert('ユーザーの追加に失敗しました')
    }
  })
}

function editBalance(userId, currentBalance, userName) {
  const content = `
    <form id="editBalanceForm">
      <div class="form-group">
        <label>ユーザー</label>
        <input type="text" value="${userName}" disabled>
      </div>
      <div class="form-group">
        <label>現在の残高</label>
        <input type="text" value="¥${currentBalance.toLocaleString()}" disabled>
      </div>
      <div class="form-group">
        <label>新しい残高 (円) *</label>
        <input type="number" id="newBalance" value="${currentBalance}" min="0" step="100" required>
      </div>
      <div class="form-actions">
        <button type="button" class="btn-secondary" onclick="hideModal()">キャンセル</button>
        <button type="submit" class="btn-warning">更新</button>
      </div>
    </form>
  `
  showModal('💰 残高編集', content)

  document.getElementById('editBalanceForm').addEventListener('submit', async (e) => {
    e.preventDefault()
    const newBalance = parseFloat(document.getElementById('newBalance').value)

    try {
      const res = await fetch(`${API_ROOT}/users/${userId}/balance?amount=${newBalance}`, {
        method: 'PATCH'
      })
      const data = await res.json()
      if (res.ok) {
        hideModal()
        refreshUsers()
        alert('残高を更新しました')
      } else {
        alert('エラー: ' + (data.message || data.detail))
      }
    } catch (error) {
      console.error(error)
      alert('残高の更新に失敗しました')
    }
  })
}

async function deleteUser(userId, userName) {
  if (!confirm(`ユーザー「${userName}」を削除しますか？\nこの操作は取り消せません。`)) {
    return
  }

  try {
    const res = await fetch(`${API_ROOT}/users/${userId}`, {
      method: 'DELETE'
    })
    if (res.ok) {
      refreshUsers()
      alert('ユーザーを削除しました')
    } else {
      const data = await res.json()
      alert('エラー: ' + (data.message || data.detail))
    }
  } catch (error) {
    console.error(error)
    alert('ユーザーの削除に失敗しました')
  }
}

// ==================== 定期券操作 ====================
async function showAddPassForm() {
  const users = await fetchUsers()
  const stations = await fetchStations()

  const userOptions = users.map(u => `<option value="${u.id}">${u.name} (ID: ${u.id})</option>`).join('')
  const stationOptions = stations.map(s => `<option value="${s.code}">${s.name || s.code} (${s.code})</option>`).join('')

  const today = new Date().toISOString().split('T')[0]
  const threeMonthsLater = new Date()
  threeMonthsLater.setMonth(threeMonthsLater.getMonth() + 3)
  const defaultEnd = threeMonthsLater.toISOString().split('T')[0]

  const content = `
    <form id="addPassForm">
      <div class="form-group">
        <label>ユーザー *</label>
        <select id="passUserId" required>
          <option value="">選択してください</option>
          ${userOptions}
        </select>
      </div>
      <div class="form-group">
        <label>種別 *</label>
        <select id="passType" required>
          <option value="commuter">通勤定期</option>
          <option value="student">通学定期</option>
        </select>
      </div>
      <div class="form-group">
        <label>開始駅 *</label>
        <select id="passStationFrom" required>
          <option value="">選択してください</option>
          ${stationOptions}
        </select>
      </div>
      <div class="form-group">
        <label>終了駅 *</label>
        <select id="passStationTo" required>
          <option value="">選択してください</option>
          ${stationOptions}
        </select>
      </div>
      <div class="form-group">
        <label>有効期間開始 *</label>
        <input type="date" id="passValidFrom" value="${today}" required>
      </div>
      <div class="form-group">
        <label>有効期間終了 *</label>
        <input type="date" id="passValidUntil" value="${defaultEnd}" required>
      </div>
      <div class="form-actions">
        <button type="button" class="btn-secondary" onclick="hideModal()">キャンセル</button>
        <button type="submit" class="btn-success">作成</button>
      </div>
    </form>
  `
  showModal('🎫 定期券追加', content)

  document.getElementById('addPassForm').addEventListener('submit', async (e) => {
    e.preventDefault()
    const user_id = parseInt(document.getElementById('passUserId').value)
    const pass_type = document.getElementById('passType').value
    const station_from = document.getElementById('passStationFrom').value
    const station_to = document.getElementById('passStationTo').value
    const valid_from = document.getElementById('passValidFrom').value + 'T00:00:00Z'
    const valid_until = document.getElementById('passValidUntil').value + 'T23:59:59Z'

    try {
      const res = await fetch(`${API_ROOT}/passes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id, pass_type, station_from, station_to, valid_from, valid_until })
      })
      const data = await res.json()
      if (res.ok) {
        hideModal()
        refreshPasses()
        alert('定期券を追加しました')
      } else {
        alert('エラー: ' + (data.message || data.detail))
      }
    } catch (error) {
      console.error(error)
      alert('定期券の追加に失敗しました')
    }
  })
}

async function deactivatePass(passId) {
  if (!confirm('この定期券を無効化しますか？')) {
    return
  }

  try {
    const res = await fetch(`${API_ROOT}/passes/${passId}/deactivate`, {
      method: 'PATCH'
    })
    const data = await res.json()
    if (res.ok) {
      refreshPasses()
      alert('定期券を無効化しました')
    } else {
      alert('エラー: ' + (data.message || data.detail))
    }
  } catch (error) {
    console.error(error)
    alert('定期券の無効化に失敗しました')
  }
}

async function deletePass(passId) {
  if (!confirm('この定期券を削除しますか？\nこの操作は取り消せません。')) {
    return
  }

  try {
    const res = await fetch(`${API_ROOT}/passes/${passId}`, {
      method: 'DELETE'
    })
    if (res.ok) {
      refreshPasses()
      alert('定期券を削除しました')
    } else {
      const data = await res.json()
      alert('エラー: ' + (data.message || data.detail))
    }
  } catch (error) {
    console.error(error)
    alert('定期券の削除に失敗しました')
  }
}

// ==================== トリップ操作 ====================
async function showAddTripForm() {
  const users = await fetchUsers()
  const stations = await fetchStations()
  const gates = await fetchGates()

  const userOptions = users.map(u => `<option value="${u.id}">${u.name} (ID: ${u.id})</option>`).join('')
  const stationOptions = stations.map(s => `<option value="${s.code}">${s.name || s.code} (${s.code})</option>`).join('')
  const gateOptions = gates.map(g => `<option value="${g.code}">${g.name || g.code} (${g.code})</option>`).join('')

  const now = new Date().toISOString().slice(0, 16)

  const content = `
    <form id="addTripForm">
      <div class="form-group">
        <label>ユーザー *</label>
        <select id="tripUserId" required>
          <option value="">選択してください</option>
          ${userOptions}
        </select>
      </div>
      <div class="form-group">
        <label>入場駅 *</label>
        <select id="tripStationIn" required>
          <option value="">選択してください</option>
          ${stationOptions}
        </select>
      </div>
      <div class="form-group">
        <label>入場ゲート *</label>
        <select id="tripGateIn" required>
          <option value="">選択してください</option>
          ${gateOptions}
        </select>
      </div>
      <div class="form-group">
        <label>入場日時 *</label>
        <input type="datetime-local" id="tripEnteredAt" value="${now}" required>
      </div>
      <div class="form-actions">
        <button type="button" class="btn-secondary" onclick="hideModal()">キャンセル</button>
        <button type="submit" class="btn-success">記録</button>
      </div>
    </form>
  `
  showModal('📝 入場記録追加', content)

  document.getElementById('addTripForm').addEventListener('submit', async (e) => {
    e.preventDefault()
    // Note: この機能は現在のAPIでは直接サポートされていません
    // /scan エンドポイントを使用する必要があります
    alert('この機能は /scan エンドポイント経由での実装が必要です')
    hideModal()
  })
}

async function showExitForm(tripId) {
  const stations = await fetchStations()
  const gates = await fetchGates()

  const stationOptions = stations.map(s => `<option value="${s.code}">${s.name || s.code} (${s.code})</option>`).join('')
  const gateOptions = gates.map(g => `<option value="${g.code}">${g.name || g.code} (${g.code})</option>`).join('')

  const now = new Date().toISOString().slice(0, 16)

  const content = `
    <form id="exitForm">
      <div class="form-group">
        <label>トリップID</label>
        <input type="text" value="${tripId}" disabled>
      </div>
      <div class="form-group">
        <label>出場駅 *</label>
        <select id="exitStationOut" required>
          <option value="">選択してください</option>
          ${stationOptions}
        </select>
      </div>
      <div class="form-group">
        <label>出場ゲート *</label>
        <select id="exitGateOut" required>
          <option value="">選択してください</option>
          ${gateOptions}
        </select>
      </div>
      <div class="form-group">
        <label>出場日時 *</label>
        <input type="datetime-local" id="exitTime" value="${now}" required>
      </div>
      <div class="form-actions">
        <button type="button" class="btn-secondary" onclick="hideModal()">キャンセル</button>
        <button type="submit" class="btn-warning">出場登録</button>
      </div>
    </form>
  `
  showModal('🚪 出場登録', content)

  document.getElementById('exitForm').addEventListener('submit', async (e) => {
    e.preventDefault()
    // Note: この機能は現在のAPIでは直接サポートされていません
    // /scan エンドポイントを使用する必要があります
    alert('この機能は /scan エンドポイント経由での実装が必要です')
    hideModal()
  })
}

async function cancelTrip(tripId) {
  if (!confirm('このトリップをキャンセルしますか？')) {
    return
  }

  try {
    const res = await fetch(`${API_ROOT}/trips/${tripId}/cancel`, {
      method: 'PATCH'
    })
    const data = await res.json()
    if (res.ok) {
      refreshTrips()
      alert('トリップをキャンセルしました')
    } else {
      alert('エラー: ' + (data.message || data.detail))
    }
  } catch (error) {
    console.error(error)
    alert('トリップのキャンセルに失敗しました')
  }
}

// ==================== イベントリスナー ====================
document.getElementById('refreshAll').addEventListener('click', refreshAll)
document.getElementById('refreshUsers').addEventListener('click', refreshUsers)
document.getElementById('refreshPasses').addEventListener('click', refreshPasses)
document.getElementById('refreshTrips').addEventListener('click', refreshTrips)
document.getElementById('refreshStations').addEventListener('click', refreshStations)
document.getElementById('refreshCards').addEventListener('click', refreshCards)

document.getElementById('addUser').addEventListener('click', showAddUserForm)
document.getElementById('addPass').addEventListener('click', showAddPassForm)
document.getElementById('addTrip').addEventListener('click', showAddTripForm)

document.getElementById('filterActivePasses').addEventListener('change', () => {
  refreshPasses()
})

document.getElementById('tripStatusFilter').addEventListener('change', () => {
  currentTripPage = 1
  renderTrips(allTrips)
})

document.getElementById('tripLimitFilter').addEventListener('change', () => {
  currentTripPage = 1
  renderTrips(allTrips)
})

// ==================== 初期読み込み ====================
refreshAll()

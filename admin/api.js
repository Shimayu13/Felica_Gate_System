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
  users.forEach(u => {
    const el = document.createElement('div')
    el.className = 'user'
    el.innerHTML = `<strong>${u.name}</strong> (id:${u.id}) - balance: ${u.balance}
      <br><button onclick="adjustBalance(${u.id})">Adjust Balance</button>`
    container.appendChild(el)
  })
}

function renderTrips(trips) {
  const container = document.getElementById('trips')
  container.innerHTML = ''
  trips.forEach(t => {
    const el = document.createElement('div')
    el.className = 'trip'
    el.innerHTML = `#${t.id} card:${t.card_id} user:${t.user_id} status:${t.status} in:${t.station_in}/${t.gate_in} out:${t.station_out || '-'} <button onclick="cancelTrip(${t.id})">Cancel</button>`
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

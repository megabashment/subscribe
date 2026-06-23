/**
 * Session persistence: cues + meta in localStorage, video file in IndexedDB.
 * IndexedDB key: 'subscribe_session_file'
 * localStorage key: 'subscribe_session'
 */

const LS_KEY = 'subscribe_session'
const IDB_DB  = 'subscribe'
const IDB_STORE = 'session'
const IDB_FILE_KEY = 'file'
const MAX_IDB_BYTES = 6 * 1024 * 1024 * 1024  // 6 GB practical upper limit

// ── localStorage helpers ────────────────────────────────────────────────────

export function saveSession({ cues, editorMeta, format }) {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify({
      cues,
      editorMeta,
      format,
      savedAt: Date.now(),
    }))
  } catch { /* quota exceeded — ignore */ }
}

export function loadSession() {
  try {
    const raw = localStorage.getItem(LS_KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch { return null }
}

export function clearSession() {
  localStorage.removeItem(LS_KEY)
  deleteSessionFile().catch(() => {})
}

// ── IndexedDB helpers ────────────────────────────────────────────────────────

function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(IDB_DB, 1)
    req.onupgradeneeded = () => req.result.createObjectStore(IDB_STORE)
    req.onsuccess = () => resolve(req.result)
    req.onerror   = () => reject(req.error)
  })
}

export async function saveSessionFile(file) {
  if (!file || file.size > MAX_IDB_BYTES) return false
  try {
    const db = await openDB()
    await new Promise((resolve, reject) => {
      const tx = db.transaction(IDB_STORE, 'readwrite')
      const req = tx.objectStore(IDB_STORE).put({ blob: file, name: file.name, type: file.type, size: file.size }, IDB_FILE_KEY)
      req.onsuccess = resolve
      req.onerror   = reject
    })
    return true
  } catch { return false }
}

export async function loadSessionFile() {
  try {
    const db = await openDB()
    const entry = await new Promise((resolve, reject) => {
      const tx  = db.transaction(IDB_STORE, 'readonly')
      const req = tx.objectStore(IDB_STORE).get(IDB_FILE_KEY)
      req.onsuccess = () => resolve(req.result)
      req.onerror   = reject
    })
    if (!entry) return null
    return new File([entry.blob], entry.name, { type: entry.type })
  } catch { return null }
}

export async function deleteSessionFile() {
  try {
    const db = await openDB()
    await new Promise((resolve, reject) => {
      const tx  = db.transaction(IDB_STORE, 'readwrite')
      const req = tx.objectStore(IDB_STORE).delete(IDB_FILE_KEY)
      req.onsuccess = resolve
      req.onerror   = reject
    })
  } catch {}
}

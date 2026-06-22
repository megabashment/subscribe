import { useState, useEffect } from 'react'
import DropZone from './components/DropZone'
import Settings from './components/Settings'
import ProgressLog from './components/ProgressLog'
import ResultPanel from './components/ResultPanel'
import styles from './App.module.css'

const API = 'http://localhost:8511'
const DEFAULT_SETTINGS = { lang: 'auto', model: 'medium', format: 'srt', device: 'auto' }

export default function App() {
  const [file, setFile] = useState(null)
  const [settings, setSettings] = useState(DEFAULT_SETTINGS)
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [apiStatus, setApiStatus] = useState(null)

  useEffect(() => {
    fetch(`${API}/health`)
      .then(r => r.json())
      .then(d => setApiStatus(d))
      .catch(() => setApiStatus(false))
  }, [])

  function reset() {
    setFile(null)
    setResult(null)
    setError(null)
  }

  async function run() {
    if (!file) return
    setRunning(true)
    setResult(null)
    setError(null)

    const form = new FormData()
    form.append('file', file)
    form.append('lang', settings.lang)
    form.append('model', settings.model)
    form.append('format', settings.format)
    form.append('device', settings.device)

    try {
      const res = await fetch(`${API}/transcribe`, { method: 'POST', body: form })

      if (!res.ok) {
        const detail = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(detail.detail || res.statusText)
      }

      const blob = await res.blob()
      const language = res.headers.get('X-Language') || '?'
      const segments = res.headers.get('X-Segments') || '?'
      const disposition = res.headers.get('Content-Disposition') || ''
      const filename = disposition.match(/filename=(.+)/)?.[1]
        || file.name.replace(/\.[^.]+$/, `.${settings.format}`)

      setResult({ blob, filename, language, segments, format: settings.format })
    } catch (e) {
      setError(e.message)
    } finally {
      setRunning(false)
    }
  }

  const canRun = file && !running && !result

  return (
    <div className={styles.app}>
      <header className={styles.header}>
        <h1 className={styles.title}>🎙️ SubScribe</h1>
        <div className={`${styles.pill} ${
          apiStatus === false ? styles.offline :
          apiStatus ? styles.online : styles.checking
        }`}>
          {apiStatus === false
            ? '⚠ API offline'
            : apiStatus
            ? `● ${apiStatus.device}`
            : '○ …'}
        </div>
      </header>

      {!result && !error && (
        <>
          <DropZone file={file} onFile={f => { setFile(f); setResult(null); setError(null) }} />
          <Settings values={settings} onChange={setSettings} disabled={running} />
        </>
      )}

      <ProgressLog running={running} />
      <ResultPanel result={result} error={error} onReset={reset} />

      {canRun && (
        <button className={styles.runBtn} onClick={run}>
          ▶&nbsp; Transkription starten
        </button>
      )}
    </div>
  )
}

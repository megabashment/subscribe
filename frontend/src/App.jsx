import { useState, useEffect, useRef, useCallback } from 'react'
import {
  IconPlayerPlay,
  IconDownload,
  IconArrowLeft,
  IconX,
  IconServer,
  IconServerOff,
  IconLoader2,
  IconSubtask,
  IconHistory,
} from '@tabler/icons-react'
import DropZone from './components/DropZone'
import Settings from './components/Settings'
import ProgressLog from './components/ProgressLog'
import ResultPanel from './components/ResultPanel'
import { Player } from './components/Player'
import { CueEditor } from './components/CueEditor'
import { StatsBar } from './components/StatsBar'
import styles from './App.module.css'
import { de, en } from './i18n'
import {
  saveSession, loadSession, clearSession,
  saveSessionFile, loadSessionFile,
} from './useSessionStore'

const API = 'http://localhost:8511'
const DEFAULT_SETTINGS = { lang: 'auto', model: 'medium', format: 'srt', device: 'auto', vad: true, beamSize: 5, prompt: '', normalize: true, denoise: false, align: false, soundEvents: false }

const FLAG_DE = '🇩🇪'
const FLAG_EN = '🇬🇧'

export default function App() {
  const [uiLang, setUiLang] = useState(() => localStorage.getItem('uiLang') || 'en')
  const t = uiLang === 'en' ? en : de

  function toggleLang() {
    const next = uiLang === 'de' ? 'en' : 'de'
    setUiLang(next)
    localStorage.setItem('uiLang', next)
  }

  const [file, setFile] = useState(null)
  const [settings, setSettings] = useState(DEFAULT_SETTINGS)
  const [view, setView] = useState('upload')
  const [error, setError] = useState(null)
  const [apiStatus, setApiStatus] = useState(null)

  const [cues, setCues] = useState([])
  const [editorMeta, setEditorMeta] = useState(null)
  const [activeCueId, setActiveCueId] = useState(null)
  const [currentTime, setCurrentTime] = useState(0)
  const [progress, setProgress] = useState(null)
  const [result, setResult] = useState(null)
  const [savedSession, setSavedSession] = useState(null)  // pending restore prompt

  const playerRef = useRef(null)
  const saveTimer = useRef(null)

  // ── Check for saved session on mount ────────────────────────────────────────
  useEffect(() => {
    const session = loadSession()
    if (session && session.cues?.length > 0) {
      setSavedSession(session)
    }
  }, [])

  useEffect(() => {
    fetch(`${API}/health`)
      .then(r => r.json())
      .then(d => setApiStatus(d))
      .catch(() => setApiStatus(false))
  }, [])

  useEffect(() => {
    const root = document.getElementById('root')
    if (root) root.classList.toggle('wide', view === 'editor')
  }, [view])

  useEffect(() => {
    const active = cues.find(c => c.start <= currentTime && c.end > currentTime)
    setActiveCueId(active ? active.id : null)
    if (active) {
      document.getElementById(`cue-${active.id}`)?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [currentTime, cues])

  // ── Auto-save cues whenever they change (debounced 1.5s) ────────────────────
  useEffect(() => {
    if (view !== 'editor' || cues.length === 0) return
    clearTimeout(saveTimer.current)
    saveTimer.current = setTimeout(() => {
      saveSession({ cues, editorMeta, format: settings.format })
    }, 1500)
    return () => clearTimeout(saveTimer.current)
  }, [cues, editorMeta, settings.format, view])

  // ── Restore saved session ────────────────────────────────────────────────────
  async function restoreSession() {
    if (!savedSession) return
    setCues(savedSession.cues)
    setEditorMeta(savedSession.editorMeta)
    if (savedSession.format) setSettings(s => ({ ...s, format: savedSession.format }))

    // Try to restore the video file from IndexedDB
    const restoredFile = await loadSessionFile()
    if (restoredFile) setFile(restoredFile)

    setSavedSession(null)
    setView('editor')
  }

  function dismissRestore() {
    setSavedSession(null)
    clearSession()
  }

  function reset() {
    clearSession()
    setFile(null); setCues([]); setEditorMeta(null)
    setResult(null); setError(null); setProgress(null)
    setSavedSession(null)
    setView('upload')
  }

  function fmtSec(s) {
    const m = Math.floor(s / 60)
    const sec = Math.floor(s % 60)
    return `${m}:${String(sec).padStart(2, '0')}`
  }

  async function runTranscription() {
    if (!file) return
    setView('running')
    setError(null)
    setProgress({ phase: 'upload', msg: '', segments: 0, uploadPct: 0, transcribePct: 0, duration: null })

    // Save file to IndexedDB for session restore
    saveSessionFile(file).catch(() => {})

    const form = new FormData()
    form.append('file', file)
    form.append('lang', settings.lang)
    form.append('model', settings.model)
    form.append('device', settings.device)
    form.append('vad', settings.vad)
    form.append('beam_size', settings.beamSize)
    form.append('prompt', settings.prompt || '')
    form.append('normalize', settings.normalize)
    form.append('denoise', settings.denoise)
    form.append('align', settings.align)
    form.append('sound_events', settings.soundEvents)

    try {
      let segmentCount = 0
      let audioDuration = null
      let sseOffset = 0
      let transcribeStartTime = null

      await new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest()
        xhr.open('POST', `${API}/transcribe/cues`)
        xhr.responseType = 'text'

        xhr.upload.onprogress = e => {
          if (!e.lengthComputable) return
          const pct = Math.round((e.loaded / e.total) * 100)
          const loadedMB = (e.loaded / 1_048_576).toFixed(1)
          const totalMB  = (e.total  / 1_048_576).toFixed(1)
          setProgress(p => ({
            ...p, phase: 'upload',
            msg: t.uploadingFile(file.name, loadedMB, totalMB),
            uploadPct: pct,
          }))
        }

        xhr.upload.onload = () => {
          setProgress(p => ({
            ...p, phase: 'start',
            msg: t.waitingForServer || 'Processing…',
            uploadPct: 100,
          }))
        }

        xhr.onprogress = () => {
          const chunk = xhr.responseText.slice(sseOffset)
          sseOffset = xhr.responseText.length
          const parts = chunk.split('\n\n')
          for (const part of parts) {
            const eventMatch = part.match(/^event: (\w+)/)
            const dataMatch  = part.match(/^data: (.+)/m)
            if (!eventMatch || !dataMatch) continue
            const event = eventMatch[1]
            let data
            try { data = JSON.parse(dataMatch[1]) } catch { continue }

            if (event === 'status') {
              if (data.duration) audioDuration = data.duration
              const phaseKey = `phase_${data.phase}`
              const phaseMsg = typeof t[phaseKey] === 'function'
                ? t[phaseKey](settings.model)
                : (t[phaseKey] || data.msg)
              setProgress(p => ({ ...p, phase: data.phase, msg: phaseMsg, duration: audioDuration }))
            } else if (event === 'download') {
              setProgress(p => ({ ...p, phase: 'download', msg: t.downloading, download: data }))
            } else if (event === 'segment') {
              if (!transcribeStartTime) transcribeStartTime = Date.now()
              segmentCount++
              const pct = audioDuration ? Math.min(99, Math.round((data.end / audioDuration) * 100)) : null

              let etaLabel = ''
              if (audioDuration && data.end > 0) {
                const elapsed = (Date.now() - transcribeStartTime) / 1000
                if (elapsed > 0.5) {
                  const speed = data.end / elapsed
                  const remaining = (audioDuration - data.end) / speed
                  if (remaining > 3) etaLabel = ` · ETA ${fmtSec(remaining)}`
                }
              }

              const timeLabel = audioDuration
                ? ` — ${fmtSec(data.end)} / ${fmtSec(audioDuration)}${etaLabel}`
                : ` — ${segmentCount} ${t.segments}`
              setProgress(p => ({
                ...p, phase: 'transcribe',
                msg: t.transcribing + timeLabel,
                segments: segmentCount,
                transcribePct: pct,
              }))
            } else if (event === 'done') {
              setCues(data.segments.map(s => ({ ...s, is_event: s.is_event ?? false })))
              setEditorMeta({ language: data.language, duration: data.duration, filename: data.filename })
              resolve('done')
            } else if (event === 'error') {
              reject(new Error(data.message))
            }
          }
        }

        xhr.onload  = () => { if (xhr.status >= 400) reject(new Error(`HTTP ${xhr.status}`)) }
        xhr.onerror = () => reject(new Error('Netzwerkfehler'))
        xhr.send(form)
      })

      setView('editor')
    } catch (e) {
      setError(e.message)
      setView('error')
    }
  }

  async function exportCues() {
    if (hasErrors) return
    try {
      const res = await fetch(`${API}/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cues,
          format: settings.format,
          filename: editorMeta?.filename || 'untertitel',
        }),
      })
      if (!res.ok) {
        const detail = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(detail.detail || res.statusText)
      }
      const blob = await res.blob()
      const filename = `${editorMeta?.filename || 'untertitel'}.${settings.format}`
      setResult({ blob, filename, language: editorMeta?.language || '?', segments: cues.length, format: settings.format })
      setView('done')
    } catch (e) {
      setError(e.message)
    }
  }

  const seek = useCallback((time) => {
    playerRef.current?.seek(time)
  }, [])

  function validateCuesLocal(c) {
    const errors = {}
    const sorted = [...c].sort((a, b) => a.start - b.start)
    for (let i = 0; i < sorted.length; i++) {
      if (sorted[i].end <= sorted[i].start) errors[sorted[i].id] = true
      if (i > 0 && sorted[i].start < sorted[i - 1].end) errors[sorted[i].id] = true
    }
    return errors
  }

  const hasErrors = Object.keys(validateCuesLocal(cues)).length > 0

  function computePillCls(device, computeType) {
    if (!computeType) return styles.online
    if (computeType === 'float16') return styles.pillFloat16
    if (computeType === 'int8_float16') return styles.pillInt8f16
    if (device === 'cuda') return styles.pillInt8gpu
    return styles.online
  }
  const apiPill = apiStatus === false
    ? { icon: <IconServerOff size={12} stroke={2} />, label: t.apiOffline, cls: styles.offline }
    : apiStatus
    ? {
        icon: <IconServer size={12} stroke={2} />,
        label: apiStatus.compute_type ? `${apiStatus.device} · ${apiStatus.compute_type}` : apiStatus.device,
        cls: computePillCls(apiStatus.device, apiStatus.compute_type),
      }
    : { icon: <IconLoader2 size={12} stroke={2} className={styles.spin} />, label: '…', cls: styles.checking }

  return (
    <div className={styles.app}>
      <header className={styles.header}>
        <div className={styles.brand}>
          <IconSubtask size={18} stroke={2} className={styles.brandIcon} />
          <h1 className={styles.title}>{t.brand}</h1>
        </div>

        {view === 'editor' && editorMeta && (
          <span className={styles.editorMeta}>
            {editorMeta.language.toUpperCase()} · {cues.length} {t.segments}
          </span>
        )}

        <button
          className={styles.langToggle}
          onClick={toggleLang}
          title={uiLang === 'de' ? 'Switch to English' : 'Auf Deutsch wechseln'}
          aria-label="Toggle language"
        >
          <span className={styles.flagActive}>{uiLang === 'de' ? FLAG_DE : FLAG_EN}</span>
          <span className={styles.flagInactive}>{uiLang === 'de' ? FLAG_EN : FLAG_DE}</span>
        </button>

        <div className={`${styles.pill} ${apiPill.cls}`}>
          {apiPill.icon}
          {apiPill.label}
        </div>
      </header>

      {/* ── Session restore banner ── */}
      {savedSession && view === 'upload' && (
        <div className={styles.restoreBanner}>
          <IconHistory size={15} stroke={2} className={styles.restoreIcon} />
          <span className={styles.restoreText}>
            {savedSession.editorMeta?.filename
              ? `"${savedSession.editorMeta.filename}" — ${savedSession.cues.length} segments`
              : `${savedSession.cues.length} segments`}
            {savedSession.savedAt && ` · ${new Date(savedSession.savedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`}
          </span>
          <button className={styles.restoreBtn} onClick={restoreSession}>Restore session</button>
          <button className={styles.restoreDismiss} onClick={dismissRestore}>
            <IconX size={12} stroke={2} />
          </button>
        </div>
      )}

      {/* ── UPLOAD ── */}
      {view === 'upload' && (
        <>
          <DropZone file={file} onFile={f => { setFile(f); setError(null) }} t={t} />
          <Settings values={settings} onChange={setSettings} disabled={false} t={t} />
          {file && (
            <button className={styles.primaryBtn} onClick={runTranscription}>
              <IconPlayerPlay size={15} stroke={2} />
              {t.startBtn}
            </button>
          )}
        </>
      )}

      {/* ── RUNNING ── */}
      {view === 'running' && (
        <>
          <ProgressLog running={true} progress={progress} t={t} />
          <StatsBar active={true} />
        </>
      )}

      {/* ── EDITOR ── */}
      {view === 'editor' && (
        <div className={styles.editorLayout}>
          {/* Player — fixed at top, full width */}
          <div style={{ flexShrink: 0 }}>
            <Player ref={playerRef} file={file} onTimeUpdate={setCurrentTime} onFileSelect={setFile} />
          </div>

          {/* Toolbar: format switcher + export + back */}
          <div className={styles.editorToolbar}>
            <div className={styles.formatRow}>
              <span className={styles.formatLabel}>{t.formatLabel}</span>
              <div className={styles.formatOptions}>
                {['srt','vtt','json'].map(f => (
                  <button
                    key={f}
                    className={`${styles.formatBtn} ${settings.format === f ? styles.formatActive : ''}`}
                    onClick={() => setSettings(s => ({ ...s, format: f }))}
                  >
                    {f.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            <button
              className={styles.primaryBtn}
              onClick={exportCues}
              disabled={hasErrors}
              title={hasErrors ? t.fixErrors : ''}
              style={{ width: 'auto', padding: '0.55rem 1rem', flexShrink: 0 }}
            >
              <IconDownload size={14} stroke={2} />
              {t.exportBtn(settings.format)}
            </button>

            <button className={styles.ghostBtn} onClick={reset} style={{ width: 'auto', padding: '0.55rem 0.9rem', flexShrink: 0 }}>
              <IconX size={13} stroke={2} />
              {t.newFile}
            </button>
          </div>

          {error && <div className={styles.inlineError} style={{ flexShrink: 0 }}>{error}</div>}

          {/* Scrollable cue editor — fills remaining height */}
          <div className={styles.editorCueList}>
            <CueEditor
              cues={cues}
              activeCueId={activeCueId}
              onCuesChange={setCues}
              onSeek={seek}
            />
          </div>
        </div>
      )}

      {/* ── DONE ── */}
      {view === 'done' && (
        <>
          <ResultPanel result={result} error={null} onReset={reset} t={t} />
          <button className={styles.ghostBtn} onClick={() => setView('editor')}>
            <IconArrowLeft size={14} stroke={2} />
            {t.backToEditor}
          </button>
        </>
      )}

      {/* ── ERROR ── */}
      {view === 'error' && (
        <ResultPanel result={null} error={error} onReset={reset} t={t} />
      )}
    </div>
  )
}

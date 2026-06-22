import { useState, useEffect, useRef } from 'react'
import {
  IconPlayerPlay,
  IconDownload,
  IconArrowLeft,
  IconX,
  IconServer,
  IconServerOff,
  IconLoader2,
  IconSubtask,
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

const API = 'http://localhost:8511'
const DEFAULT_SETTINGS = { lang: 'auto', model: 'medium', format: 'srt', device: 'auto', vad: true, beamSize: 5, prompt: '', normalize: true, denoise: false, align: false }

const FLAG_DE = '🇩🇪'
const FLAG_EN = '🇬🇧'

export default function App() {
  const [uiLang, setUiLang] = useState(() => localStorage.getItem('uiLang') || 'de')
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

  const playerRef = useRef(null)

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

  function reset() {
    setFile(null); setCues([]); setEditorMeta(null)
    setResult(null); setError(null); setProgress(null)
    setView('upload')
  }

  async function runTranscription() {
    if (!file) return
    setView('running')
    setError(null)
    setProgress({ phase: 'start', msg: t.connecting, segments: 0 })

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

    try {
      const res = await fetch(`${API}/transcribe/cues`, { method: 'POST', body: form })
      if (!res.ok) {
        const detail = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(detail.detail || res.statusText)
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buf = ''
      let segmentCount = 0

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buf += decoder.decode(value, { stream: true })
        const parts = buf.split('\n\n')
        buf = parts.pop()

        for (const part of parts) {
          const eventMatch = part.match(/^event: (\w+)/)
          const dataMatch = part.match(/^data: (.+)/m)
          if (!eventMatch || !dataMatch) continue
          const event = eventMatch[1]
          const data = JSON.parse(dataMatch[1])

          if (event === 'status') {
            setProgress(p => ({ ...p, phase: data.phase, msg: data.msg }))
          } else if (event === 'download') {
            setProgress(p => ({ ...p, phase: 'download', msg: t.downloading, download: data }))
          } else if (event === 'segment') {
            segmentCount++
            setProgress(p => ({ ...p, phase: 'transcribe', msg: t.transcribing, segments: segmentCount }))
          } else if (event === 'done') {
            setCues(data.segments)
            setEditorMeta({ language: data.language, duration: data.duration, filename: data.filename })
            setView('editor')
            return
          } else if (event === 'error') {
            throw new Error(data.message)
          }
        }
      }
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

  function seek(time) {
    const el = playerRef.current?.querySelector('video, audio')
    if (el) el.currentTime = time
  }

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

  // API status pill content
  const apiPill = apiStatus === false
    ? { icon: <IconServerOff size={12} stroke={2} />, label: t.apiOffline, cls: styles.offline }
    : apiStatus
    ? { icon: <IconServer size={12} stroke={2} />, label: apiStatus.device, cls: styles.online }
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

      {/* ── UPLOAD ── */}
      {view === 'upload' && (
        <>
          <DropZone file={file} onFile={f => { setFile(f); setError(null) }} />
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
          <div className={styles.editorLeft}>
            <div ref={playerRef}>
              <Player file={file} cues={cues} activeCueId={activeCueId} onTimeUpdate={setCurrentTime} />
            </div>

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
            >
              <IconDownload size={15} stroke={2} />
              {t.exportBtn(settings.format)}
            </button>

            <button className={styles.ghostBtn} onClick={reset}>
              <IconX size={14} stroke={2} />
              {t.newFile}
            </button>

            {error && <div className={styles.inlineError}>{error}</div>}
          </div>

          <div className={styles.editorRight}>
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
          <ResultPanel result={result} error={null} onReset={reset} />
          <button className={styles.ghostBtn} onClick={() => setView('editor')}>
            <IconArrowLeft size={14} stroke={2} />
            {t.backToEditor}
          </button>
        </>
      )}

      {/* ── ERROR ── */}
      {view === 'error' && (
        <ResultPanel result={null} error={error} onReset={reset} />
      )}
    </div>
  )
}

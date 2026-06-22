import { useState, useCallback } from "react"
import {
  IconPlayerPlay,
  IconScissors,
  IconArrowMerge,
  IconTrash,
  IconAlertTriangle,
  IconAlertCircle,
} from "@tabler/icons-react"
import styles from "./CueEditor.module.css"

const LINE_WARN = 42

function parseTime(val) {
  // accepts HH:MM:SS.mmm or plain seconds
  if (typeof val === "number") return val
  const parts = val.split(":")
  if (parts.length === 3) {
    return parseFloat(parts[0]) * 3600 + parseFloat(parts[1]) * 60 + parseFloat(parts[2])
  }
  return parseFloat(val) || 0
}

function fmtTime(sec) {
  const ms = Math.round(sec * 1000)
  const h = Math.floor(ms / 3_600_000)
  const m = Math.floor((ms % 3_600_000) / 60_000)
  const s = Math.floor((ms % 60_000) / 1_000)
  const ms3 = ms % 1_000
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}.${String(ms3).padStart(3, "0")}`
}

function validateCues(cues) {
  const errors = {}
  for (let i = 0; i < cues.length; i++) {
    const c = cues[i]
    if (c.end <= c.start) {
      errors[c.id] = `Ende (${fmtTime(c.end)}) muss nach Start (${fmtTime(c.start)}) liegen`
    } else if (i > 0 && c.start < cues[i - 1].end) {
      errors[c.id] = `Überlappung mit Cue ${cues[i - 1].id + 1} (endet ${fmtTime(cues[i - 1].end)})`
    }
  }
  return errors
}

export function CueEditor({ cues, activeCueId, onCuesChange, onSeek }) {
  const [errors, setErrors] = useState({})

  const update = useCallback((id, field, raw) => {
    const updated = cues.map(c => {
      if (c.id !== id) return c
      const val = field === "text" ? raw : parseTime(raw)
      return { ...c, [field]: val }
    })
    setErrors(validateCues(updated))
    onCuesChange(updated)
  }, [cues, onCuesChange])

  function deleteCue(id) {
    const updated = cues.filter(c => c.id !== id)
    setErrors(validateCues(updated))
    onCuesChange(updated)
  }

  function splitCue(id) {
    const idx = cues.findIndex(c => c.id === id)
    const c = cues[idx]
    const mid = (c.start + c.end) / 2
    const half = Math.floor(c.text.length / 2)
    const nextId = Math.max(...cues.map(x => x.id)) + 1
    const left = { ...c, end: mid, text: c.text.slice(0, half).trim() }
    const right = { ...c, id: nextId, start: mid, text: c.text.slice(half).trim() }
    const updated = [...cues.slice(0, idx), left, right, ...cues.slice(idx + 1)]
    setErrors(validateCues(updated))
    onCuesChange(updated)
  }

  function mergeCue(id) {
    const idx = cues.findIndex(c => c.id === id)
    if (idx >= cues.length - 1) return
    const a = cues[idx]
    const b = cues[idx + 1]
    const merged = { ...a, end: b.end, text: `${a.text} ${b.text}`.trim() }
    const updated = [...cues.slice(0, idx), merged, ...cues.slice(idx + 2)]
    setErrors(validateCues(updated))
    onCuesChange(updated)
  }

  const hasErrors = Object.keys(errors).length > 0

  return (
    <div className={styles.editor}>
      {hasErrors && (
        <div className={styles.globalError}>
          <IconAlertCircle size={13} stroke={2} />
          {Object.keys(errors).length} Zeitfehler — Export gesperrt
        </div>
      )}
      <div className={styles.list}>
        {cues.map((cue, idx) => {
          const err = errors[cue.id]
          const isActive = cue.id === activeCueId
          const isEvent = cue.is_event === true
          const maxLineLen = Math.max(...cue.text.split("\n").map(l => l.length))
          const lineWarn = !isEvent && maxLineLen > LINE_WARN

          return (
            <div
              key={cue.id}
              className={`${styles.cue} ${isActive ? styles.active : ""} ${err ? styles.hasError : ""} ${isEvent ? styles.isEvent : ""}`}
              id={`cue-${cue.id}`}
            >
              <div className={styles.cueHeader}>
                <span className={styles.cueNum}>{idx + 1}</span>
                <input
                  className={styles.timeInput}
                  defaultValue={fmtTime(cue.start)}
                  onBlur={e => update(cue.id, "start", e.target.value)}
                  title="Start"
                />
                <span className={styles.arrow}>→</span>
                <input
                  className={styles.timeInput}
                  defaultValue={fmtTime(cue.end)}
                  onBlur={e => update(cue.id, "end", e.target.value)}
                  title="Ende"
                />
                <button
                  className={styles.seekBtn}
                  onClick={() => onSeek(cue.start)}
                  title="Abspielen ab hier"
                >
                  <IconPlayerPlay size={10} stroke={2} />
                </button>
                <div className={styles.actions}>
                  <button onClick={() => splitCue(cue.id)} title="Segment teilen">
                    <IconScissors size={12} stroke={1.5} />
                  </button>
                  {idx < cues.length - 1 && (
                    <button onClick={() => mergeCue(cue.id)} title="Mit nächstem zusammenführen">
                      <IconArrowMerge size={12} stroke={1.5} />
                    </button>
                  )}
                  <button onClick={() => deleteCue(cue.id)} title="Löschen" className={styles.deleteBtn}>
                    <IconTrash size={12} stroke={1.5} />
                  </button>
                </div>
              </div>

              <textarea
                className={styles.textArea}
                defaultValue={cue.text}
                rows={Math.max(2, cue.text.split("\n").length)}
                onBlur={e => update(cue.id, "text", e.target.value)}
              />

              {(lineWarn || err) && (
                <div className={styles.cueFooter}>
                  {lineWarn && (
                    <span className={styles.charWarn}>
                      <IconAlertTriangle size={11} stroke={2} />
                      Zeile &gt;{LINE_WARN} Zeichen
                    </span>
                  )}
                  {err && (
                    <span className={styles.errorMsg}>
                      <IconAlertCircle size={11} stroke={2} />
                      {err}
                    </span>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export function useCueErrors(cues) {
  return validateCues(cues)
}

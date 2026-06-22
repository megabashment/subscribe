import { useState, useEffect, useRef } from 'react'
import {
  IconChevronDown,
  IconCircleCheck,
  IconCircleArrowDown,
  IconBolt,
  IconStar,
  IconSettings2,
} from '@tabler/icons-react'
import styles from './Settings.module.css'

const API = 'http://localhost:8511'

// Primary: auto-detect + DE/EN/ES. Optional: JP (needs large-v3 for best results).
// All other languages Whisper detects automatically via 'auto' — no explicit listing needed.
const LANGUAGES = [
  { code: 'auto', label: 'Auto-detect' },
  { code: 'en',   label: 'English' },
  { code: 'de',   label: 'Deutsch' },
  { code: 'es',   label: 'Español' },
  { code: 'ja',   label: '日本語 (JP)', note: 'large-v3 recommended' },
]
const FORMATS = ['srt','vtt','json']
const DEVICES = ['auto','cuda','cpu']
const BEAM_PRESETS = [1, 5, 10]  // Schnell | Standard | Genau

const MODEL_META = {
  'tiny':     { size: 0.15, speed: '~32×', quality: 1, recommended: false },
  'base':     { size: 0.29, speed: '~16×', quality: 2, recommended: false },
  'small':    { size: 0.97, speed: '~6×',  quality: 3, recommended: false },
  'medium':   { size: 3.1,  speed: '~2×',  quality: 4, recommended: true },
  'large-v3': { size: 6.2,  speed: '1×',   quality: 5, recommended: false },
}

function QualityDots({ level, max = 5 }) {
  return (
    <span className={styles.dots}>
      {Array.from({ length: max }, (_, i) => (
        <span key={i} className={i < level ? styles.dotOn : styles.dotOff} />
      ))}
    </span>
  )
}

function ModelSelect({ value, onChange, disabled, t }) {
  const [open, setOpen] = useState(false)
  const [modelInfo, setModelInfo] = useState({})
  const ref = useRef(null)

  useEffect(() => {
    fetch(`${API}/models`).then(r => r.json()).then(setModelInfo).catch(() => {})
  }, [])

  useEffect(() => {
    function onClickOut(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOut)
    return () => document.removeEventListener('mousedown', onClickOut)
  }, [])

  const meta = MODEL_META[value]
  const info = modelInfo[value]
  const panelRef = useRef(null)

  // Flip panel to right-align if it overflows the viewport
  useEffect(() => {
    if (!open || !panelRef.current) return
    const rect = panelRef.current.getBoundingClientRect()
    if (rect.right > window.innerWidth - 12) {
      panelRef.current.style.left = 'auto'
      panelRef.current.style.right = '0'
    }
  }, [open])

  return (
    <div ref={ref} className={styles.modelWrap}>
      <button
        type="button"
        className={styles.modelTrigger}
        onClick={() => !disabled && setOpen(o => !o)}
        disabled={disabled}
      >
        <span className={styles.triggerName}>{value}</span>
        {info?.cached
          ? <span className={styles.cachedPill}><IconCircleCheck size={11} /> {t.localPill}</span>
          : info && <span className={styles.dlPill}><IconCircleArrowDown size={11} /> {meta?.size} GB</span>
        }
        <IconChevronDown size={13} className={`${styles.chevron} ${open ? styles.chevronOpen : ''}`} />
      </button>

      {open && (
        <div className={styles.panel} ref={panelRef}>
          {Object.entries(MODEL_META).map(([name, m]) => {
            const mi = modelInfo[name]
            const cached = mi?.cached
            const active = name === value
            const lm = t.modelMeta[name] || {}
            return (
              <div
                key={name}
                className={`${styles.item} ${active ? styles.itemActive : ''}`}
                onClick={() => { onChange(name); setOpen(false) }}
              >
                {/* Left: name + quality */}
                <div className={styles.itemLeft}>
                  <div className={styles.itemNameRow}>
                    <span className={styles.itemName}>{name}</span>
                    {m.recommended && <span className={styles.rec}><IconStar size={9} /> {t.recommended}</span>}
                  </div>
                  <QualityDots level={m.quality} />
                </div>

                {/* Center: speed + use-case */}
                <div className={styles.itemCenter}>
                  <span className={styles.speed}><IconBolt size={11} />{m.speed}</span>
                  <span className={styles.useCase}>{lm.use}</span>
                </div>

                {/* Right: pros/cons + cache badge */}
                <div className={styles.itemRight}>
                  <div className={styles.procons}>
                    {(lm.pros || []).map(p => <div key={p} className={styles.pro}>+ {p}</div>)}
                    {(lm.cons || []).map(c => <div key={c} className={styles.con}>– {c}</div>)}
                  </div>
                  {cached
                    ? <span className={styles.cachedPill}><IconCircleCheck size={11} /> {t.localPill}</span>
                    : <span className={styles.dlPill}><IconCircleArrowDown size={11} /> {m.size} GB</span>
                  }
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default function Settings({ values, onChange, disabled, t = {} }) {
  const [showAdvanced, setShowAdvanced] = useState(false)

  function set(key) {
    return e => onChange({ ...values, [key]: e.target.value })
  }

  const hasNonDefault = values.device !== 'auto' || !values.vad || values.beamSize !== 5
    || values.prompt || !values.normalize || values.denoise || values.align || values.soundEvents

  return (
    <div className={styles.bar}>
      {/* ── Core settings ── */}
      <div className={styles.coreRow}>
        <label className={styles.field}>
          <span>{t.langLabel}</span>
          <select value={values.lang} onChange={set('lang')} disabled={disabled}>
            {LANGUAGES.map(l => (
              <option key={l.code} value={l.code}>{l.label}</option>
            ))}
          </select>
          {values.lang === 'ja' && values.model !== 'large-v3' && (
            <span className={styles.langHint}>{t.jpHint || '⚠ large-v3 recommended'}</span>
          )}
        </label>

        <label className={styles.field}>
          <span>{t.modelLabel}</span>
          <ModelSelect value={values.model} onChange={m => onChange({ ...values, model: m })} disabled={disabled} t={t} />
        </label>

        <label className={styles.field}>
          <span>{t.formatLabel}</span>
          <select value={values.format} onChange={set('format')} disabled={disabled}>
            {FORMATS.map(f => <option key={f} value={f}>{f.toUpperCase()}</option>)}
          </select>
        </label>

        <button
          type="button"
          className={`${styles.advancedToggle} ${showAdvanced ? styles.advancedOpen : ''} ${hasNonDefault ? styles.advancedDirty : ''}`}
          onClick={() => setShowAdvanced(v => !v)}
          title={t.advancedTitle || 'Advanced settings'}
          disabled={disabled}
        >
          <IconSettings2 size={13} stroke={1.8} />
          <span>{t.advanced || 'Advanced'}</span>
          <IconChevronDown size={11} className={`${styles.chevron} ${showAdvanced ? styles.chevronOpen : ''}`} />
        </button>
      </div>

      {/* ── Advanced settings ── */}
      {showAdvanced && (
        <div className={styles.advancedRow}>
          <label className={styles.field}>
            <span>{t.deviceLabel}</span>
            <select value={values.device} onChange={set('device')} disabled={disabled}>
              {DEVICES.map(d => <option key={d} value={d}>{d}</option>)}
            </select>
          </label>

          <label className={`${styles.field} ${styles.toggleField}`} title={t.vadTitle}>
            <span>{t.vadLabel}</span>
            <button
              type="button"
              className={`${styles.toggle} ${values.vad ? styles.toggleOn : ''}`}
              onClick={() => !disabled && onChange({ ...values, vad: !values.vad })}
              disabled={disabled}
            >
              {values.vad ? t.vadOn : t.vadOff}
            </button>
          </label>

          <label className={styles.field} title={t.qualityTitle}>
            <span>{t.qualityLabel}</span>
            <select
              value={values.beamSize}
              onChange={e => onChange({ ...values, beamSize: Number(e.target.value) })}
              disabled={disabled}
            >
              <option value={BEAM_PRESETS[0]}>{t.qualityFast}</option>
              <option value={BEAM_PRESETS[1]}>{t.qualityStandard}</option>
              <option value={BEAM_PRESETS[2]}>{t.qualityAccurate}</option>
            </select>
          </label>

          <label className={`${styles.field} ${styles.promptField}`} title={t.promptTitle}>
            <span>{t.promptLabel}</span>
            <input
              type="text"
              value={values.prompt}
              onChange={set('prompt')}
              placeholder={t.promptPlaceholder}
              disabled={disabled}
            />
          </label>

          <label className={`${styles.field} ${styles.toggleField}`} title={t.normalizeTitle}>
            <span>{t.normalizeLabel}</span>
            <button
              type="button"
              className={`${styles.toggle} ${values.normalize ? styles.toggleOn : ''}`}
              onClick={() => !disabled && onChange({ ...values, normalize: !values.normalize })}
              disabled={disabled}
            >
              {values.normalize ? t.on : t.off}
            </button>
          </label>

          <label className={`${styles.field} ${styles.toggleField}`} title={t.denoiseTitle}>
            <span>{t.denoiseLabel}</span>
            <button
              type="button"
              className={`${styles.toggle} ${values.denoise ? styles.toggleOn : ''}`}
              onClick={() => !disabled && onChange({ ...values, denoise: !values.denoise })}
              disabled={disabled}
            >
              {values.denoise ? t.on : t.off}
            </button>
          </label>

          <label className={`${styles.field} ${styles.toggleField}`} title={t.alignTitle}>
            <span>{t.alignLabel}</span>
            <button
              type="button"
              className={`${styles.toggle} ${values.align ? styles.toggleOn : ''}`}
              onClick={() => !disabled && onChange({ ...values, align: !values.align })}
              disabled={disabled}
            >
              {values.align ? t.on : t.off}
            </button>
          </label>

          <label className={`${styles.field} ${styles.toggleField}`} title={t.soundEventsTitle}>
            <span>{t.soundEventsLabel}</span>
            <button
              type="button"
              className={`${styles.toggle} ${values.soundEvents ? styles.toggleOn : ''}`}
              onClick={() => !disabled && onChange({ ...values, soundEvents: !values.soundEvents })}
              disabled={disabled}
            >
              {values.soundEvents ? t.on : t.off}
            </button>
          </label>
        </div>
      )}
    </div>
  )
}

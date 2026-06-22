import styles from './Settings.module.css'

const LANGUAGES = ['auto','de','en','fr','es','it','pl','nl','pt','ru','zh','ja']
const MODELS = ['tiny','base','small','medium','large-v3']
const FORMATS = ['srt','vtt','json']
const DEVICES = ['auto','cuda','cpu']

export default function Settings({ values, onChange, disabled }) {
  function set(key) {
    return e => onChange({ ...values, [key]: e.target.value })
  }

  return (
    <div className={styles.bar}>
      <label className={styles.field}>
        <span>Sprache</span>
        <select value={values.lang} onChange={set('lang')} disabled={disabled}>
          {LANGUAGES.map(l => <option key={l} value={l}>{l}</option>)}
        </select>
      </label>
      <label className={styles.field}>
        <span>Modell</span>
        <select value={values.model} onChange={set('model')} disabled={disabled}>
          {MODELS.map(m => <option key={m} value={m}>{m}</option>)}
        </select>
      </label>
      <label className={styles.field}>
        <span>Format</span>
        <select value={values.format} onChange={set('format')} disabled={disabled}>
          {FORMATS.map(f => <option key={f} value={f}>{f}</option>)}
        </select>
      </label>
      <label className={styles.field}>
        <span>Gerät</span>
        <select value={values.device} onChange={set('device')} disabled={disabled}>
          {DEVICES.map(d => <option key={d} value={d}>{d}</option>)}
        </select>
      </label>
    </div>
  )
}

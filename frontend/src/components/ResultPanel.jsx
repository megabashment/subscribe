import styles from './ResultPanel.module.css'

export default function ResultPanel({ result, error, onReset }) {
  if (error) {
    return (
      <div className={`${styles.wrap} ${styles.errWrap}`}>
        <div className={styles.errTitle}>Fehler</div>
        <div className={styles.errMsg}>{error}</div>
        <button className={styles.resetBtn} onClick={onReset}>Nochmal versuchen</button>
      </div>
    )
  }

  if (!result) return null

  function download() {
    const url = URL.createObjectURL(result.blob)
    const a = document.createElement('a')
    a.href = url
    a.download = result.filename
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className={styles.wrap}>
      <div className={styles.metrics}>
        <div className={styles.metric}>
          <span className={styles.val}>{result.language.toUpperCase()}</span>
          <span className={styles.key}>Sprache</span>
        </div>
        <div className={styles.metric}>
          <span className={styles.val}>{result.segments}</span>
          <span className={styles.key}>Segmente</span>
        </div>
        <div className={styles.metric}>
          <span className={styles.val}>{result.format.toUpperCase()}</span>
          <span className={styles.key}>Format</span>
        </div>
      </div>
      <button className={styles.dlBtn} onClick={download}>
        ⬇ {result.filename} herunterladen
      </button>
      <button className={styles.resetBtn} onClick={onReset}>Neue Datei</button>
    </div>
  )
}

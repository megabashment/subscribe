import { IconDownload, IconAlertCircle, IconLanguage, IconList, IconFileText } from '@tabler/icons-react'
import styles from './ResultPanel.module.css'

export default function ResultPanel({ result, error, onReset, t = {} }) {
  if (error) {
    return (
      <div className={`${styles.wrap} ${styles.errWrap}`}>
        <div className={styles.errHeader}>
          <IconAlertCircle size={16} stroke={2} />
          <span>{t.resultError || 'Error'}</span>
        </div>
        <p className={styles.errMsg}>{error}</p>
        <button className={styles.secondaryBtn} onClick={onReset}>
          {t.resultRetry || 'Try again'}
        </button>
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
          <IconLanguage size={14} stroke={1.5} className={styles.metricIcon} />
          <span className={styles.metricVal}>{result.language.toUpperCase()}</span>
          <span className={styles.metricKey}>{t.resultLang || 'Language'}</span>
        </div>
        <div className={styles.metric}>
          <IconList size={14} stroke={1.5} className={styles.metricIcon} />
          <span className={styles.metricVal}>{result.segments}</span>
          <span className={styles.metricKey}>{t.resultSegments || 'Segments'}</span>
        </div>
        <div className={styles.metric}>
          <IconFileText size={14} stroke={1.5} className={styles.metricIcon} />
          <span className={styles.metricVal}>{result.format.toUpperCase()}</span>
          <span className={styles.metricKey}>{t.resultFormat || 'Format'}</span>
        </div>
      </div>
      <button className={styles.primaryBtn} onClick={download}>
        <IconDownload size={15} stroke={2} />
        {typeof t.resultDownload === 'function' ? t.resultDownload(result.format) : `Download ${result.format.toUpperCase()}`}
      </button>
      <p className={styles.filename}>{result.filename}</p>
      <button className={styles.secondaryBtn} onClick={onReset}>
        {t.newFile || 'New file'}
      </button>
    </div>
  )
}

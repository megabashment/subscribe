import styles from './ProgressLog.module.css'

export default function ProgressLog({ running, progress, t }) {
  if (!running) return null

  const phase = progress?.phase || 'start'
  const dl = progress?.download
  const uploadPct = progress?.uploadPct ?? null
  const transcribePct = progress?.transcribePct ?? null

  const showUploadBar = phase === 'upload' && uploadPct !== null
  const showTranscribeBar = phase === 'transcribe' && transcribePct !== null
  const showDeterminate = showUploadBar || showTranscribeBar
  const determinatePct = showUploadBar ? uploadPct : transcribePct

  return (
    <div className={styles.wrap}>
      <div className={styles.row}>
        <span className={styles.spinner} />
        <span className={styles.label}>{progress?.msg || t?.connecting || 'Connecting…'}</span>
        {showDeterminate && <span className={styles.pct}>{determinatePct}%</span>}
        {phase === 'download' && dl && (
          <span className={styles.pct}>{dl.downloaded_mb} / {dl.total_mb ?? '?'} MB</span>
        )}
      </div>

      {/* Determinate bar — upload, transcribe, or model download */}
      {showDeterminate && (
        <div className={styles.track}>
          <div className={styles.bar} style={{ width: `${determinatePct}%`, transition: 'width 0.3s ease' }} />
        </div>
      )}
      {phase === 'download' && dl && dl.total_mb && (
        <div className={styles.track}>
          <div className={styles.bar} style={{ width: `${Math.min(100, (dl.downloaded_mb / dl.total_mb) * 100)}%`, transition: 'width 0.4s ease' }} />
        </div>
      )}

      {/* Indeterminate bar for phases with no progress data */}
      {!showDeterminate && phase !== 'download' && (
        <div className={styles.track}>
          <div className={styles.barIndeterminate} />
        </div>
      )}
    </div>
  )
}

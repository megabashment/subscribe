import {
  IconDownload,
  IconSparkles,
  IconFileMusic,
  IconAlignJustified,
  IconUpload,
} from '@tabler/icons-react'
import styles from './ProgressLog.module.css'

const PHASE_ICONS = {
  upload:     IconUpload,
  start:      IconSparkles,
  model:      IconSparkles,
  download:   IconDownload,
  audio:      IconFileMusic,
  transcribe: IconAlignJustified,
  align:      IconAlignJustified,
}

export default function ProgressLog({ running, progress, t }) {
  if (!running) return null

  const phase = progress?.phase || 'start'
  const Icon = PHASE_ICONS[phase] || IconSparkles
  const dl = progress?.download
  const uploadPct = progress?.uploadPct ?? null
  const transcribePct = progress?.transcribePct ?? null

  // Determinate bar: upload or transcribe with known duration
  const showUploadBar = phase === 'upload' && uploadPct !== null
  const showTranscribeBar = phase === 'transcribe' && transcribePct !== null
  const showDeterminate = showUploadBar || showTranscribeBar
  const determinatePct = showUploadBar ? uploadPct : transcribePct

  return (
    <div className={styles.wrap}>
      <div className={styles.row}>
        <span className={styles.spinner} />
        <Icon size={15} className={styles.phaseIcon} />
        <span className={styles.label}>{progress?.msg || t?.connecting || 'Connecting…'}</span>
      </div>

      {/* Download progress (determinate) */}
      {phase === 'download' && dl && (
        <div className={styles.downloadRow}>
          <div className={styles.track}>
            <div
              className={styles.bar}
              style={{
                width: dl.total_mb
                  ? `${Math.min(100, (dl.downloaded_mb / dl.total_mb) * 100)}%`
                  : '0%',
                transition: 'width 0.4s ease',
              }}
            />
          </div>
          <span className={styles.dlNumbers}>
            {dl.downloaded_mb} / {dl.total_mb ?? '?'} MB
          </span>
        </div>
      )}

      {/* Upload or transcribe — determinate bar */}
      {showDeterminate && (
        <div className={styles.progressRow}>
          <div className={styles.track}>
            <div
              className={styles.bar}
              style={{ width: `${determinatePct}%`, transition: 'width 0.3s ease' }}
            />
          </div>
          <span className={styles.pct}>{determinatePct}%</span>
        </div>
      )}

      {/* Indeterminate bar for phases without progress info */}
      {!showDeterminate && phase !== 'download' && (
        <div className={styles.track}>
          <div className={styles.barIndeterminate} />
        </div>
      )}
    </div>
  )
}

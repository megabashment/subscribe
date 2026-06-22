import {
  IconDownload,
  IconSparkles,
  IconFileMusic,
  IconAlignJustified,
} from '@tabler/icons-react'
import styles from './ProgressLog.module.css'

const PHASE_ICONS = {
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
  const segLabel = t ? `${progress?.segments} ${t.segments}` : `${progress?.segments} Segmente erkannt`

  return (
    <div className={styles.wrap}>
      <div className={styles.row}>
        <span className={styles.spinner} />
        <Icon size={15} className={styles.phaseIcon} />
        <span className={styles.label}>{progress?.msg || t?.connecting || 'Connecting…'}</span>
      </div>

      {/* Download progress */}
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

      {/* Indeterminate bar for all other phases */}
      {phase !== 'download' && (
        <div className={styles.track}>
          <div className={styles.barIndeterminate} />
        </div>
      )}

      {/* Segment counter during transcription */}
      {phase === 'transcribe' && progress?.segments > 0 && (
        <div className={styles.segCount}>{segLabel}</div>
      )}
    </div>
  )
}

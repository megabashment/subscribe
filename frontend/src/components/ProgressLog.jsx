import styles from './ProgressLog.module.css'

export default function ProgressLog({ running }) {
  if (!running) return null

  return (
    <div className={styles.wrap}>
      <div className={styles.spinner} />
      <div className={styles.label}>Transkription läuft…</div>
      <div className={styles.track}>
        <div className={styles.bar} />
      </div>
      <div className={styles.hint}>
        Beim ersten Mal wird das Modell heruntergeladen (~300 MB – 1.5 GB). Danach startet es sofort.
      </div>
    </div>
  )
}

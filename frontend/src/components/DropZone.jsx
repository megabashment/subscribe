import { useRef, useState } from 'react'
import styles from './DropZone.module.css'

const ACCEPTED = ['mp4','mkv','mov','avi','mp3','wav','m4a','flac']

export default function DropZone({ file, onFile }) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef()

  function handleDrop(e) {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) onFile(f)
  }

  function handleChange(e) {
    const f = e.target.files[0]
    if (f) onFile(f)
  }

  return (
    <div
      className={`${styles.zone} ${dragging ? styles.dragging : ''} ${file ? styles.filled : ''}`}
      onDragOver={e => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED.map(e => `.${e}`).join(',')}
        style={{ display: 'none' }}
        onChange={handleChange}
      />
      {file ? (
        <div className={styles.fileInfo}>
          <span className={styles.icon}>🎬</span>
          <div>
            <div className={styles.filename}>{file.name}</div>
            <div className={styles.meta}>{(file.size / 1_048_576).toFixed(1)} MB</div>
          </div>
          <button
            className={styles.clear}
            onClick={e => { e.stopPropagation(); onFile(null) }}
          >✕</button>
        </div>
      ) : (
        <div className={styles.empty}>
          <span className={styles.icon}>🎙️</span>
          <div className={styles.label}>Datei hierher ziehen</div>
          <div className={styles.sub}>oder klicken zum Auswählen · {ACCEPTED.join(', ')}</div>
        </div>
      )}
    </div>
  )
}

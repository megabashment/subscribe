import { useState, useRef } from 'react'
import { IconUpload, IconFileMusic, IconVideo, IconX } from '@tabler/icons-react'
import styles from './DropZone.module.css'

const ACCEPTED = ['mp4','mkv','mov','avi','mp3','wav','m4a','flac','webm','ogg']

function fmtSize(bytes) {
  if (bytes < 1_048_576) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / 1_048_576).toFixed(1)} MB`
}

export default function DropZone({ file, onFile, t = {} }) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef()

  function handleDrop(e) {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) onFile(f)
  }

  const isVideo = file?.type?.startsWith('video/')

  return (
    <div
      className={`${styles.zone} ${dragging ? styles.dragging : ''} ${file ? styles.filled : ''}`}
      onDragOver={e => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => !file && inputRef.current.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED.map(e => `.${e}`).join(',')}
        style={{ display: 'none' }}
        onChange={e => e.target.files[0] && onFile(e.target.files[0])}
      />

      {file ? (
        <div className={styles.fileRow}>
          <span className={styles.fileIcon}>
            {isVideo ? <IconVideo size={18} stroke={1.5} /> : <IconFileMusic size={18} stroke={1.5} />}
          </span>
          <div className={styles.fileMeta}>
            <span className={styles.fileName}>{file.name}</span>
            <span className={styles.fileSize}>{fmtSize(file.size)}</span>
          </div>
          <button
            className={styles.clearBtn}
            onClick={e => { e.stopPropagation(); onFile(null) }}
            title={t.dropClear || 'Remove file'}
          >
            <IconX size={13} stroke={2} />
          </button>
        </div>
      ) : (
        <div className={styles.empty}>
          <IconUpload size={26} stroke={1.5} className={styles.uploadIcon} />
          <span className={styles.label}>{t.dropLabel || 'Drop file here'}</span>
          <span className={styles.sub}>{t.dropSub || 'or click to browse'} · {ACCEPTED.join(', ')}</span>
        </div>
      )}
    </div>
  )
}

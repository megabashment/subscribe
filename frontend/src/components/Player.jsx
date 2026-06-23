import { useEffect, useRef, useMemo, useImperativeHandle, forwardRef } from "react"
import { IconFolderOpen } from "@tabler/icons-react"
import styles from "./Player.module.css"

export const Player = forwardRef(function Player({ file, onTimeUpdate, onFileSelect }, ref) {
  const mediaRef = useRef(null)

  // Stable object URL — only recreated when file changes
  const url = useMemo(() => {
    return file ? URL.createObjectURL(file) : null
  }, [file])

  useEffect(() => {
    return () => { if (url) URL.revokeObjectURL(url) }
  }, [url])

  // Expose seek() to parent via ref
  useImperativeHandle(ref, () => ({
    seek(time) {
      if (mediaRef.current) {
        mediaRef.current.currentTime = time
      }
    }
  }), [])

  function handleTimeUpdate() {
    if (mediaRef.current) onTimeUpdate(mediaRef.current.currentTime)
  }

  function handleFileInput(e) {
    const f = e.target.files?.[0]
    if (f && onFileSelect) onFileSelect(f)
  }

  const isVideo = file && file.type.startsWith("video/")
  const MediaEl = isVideo ? "video" : "audio"

  return (
    <div className={styles.player}>
      {url
        ? <MediaEl
            key={url}
            ref={mediaRef}
            src={url}
            controls
            className={isVideo ? styles.video : styles.audio}
            onTimeUpdate={handleTimeUpdate}
          />
        : <label className={styles.noFile}>
            <IconFolderOpen size={18} stroke={1.5} className={styles.noFileIcon} />
            <span className={styles.noFileLabel}>Load video file</span>
            <span className={styles.noFileHint}>Select your original file to enable playback</span>
            <input
              type="file"
              accept="video/*,audio/*"
              className={styles.fileInput}
              onChange={handleFileInput}
            />
          </label>
      }
    </div>
  )
})

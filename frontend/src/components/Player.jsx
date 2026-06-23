import { useEffect, useRef, useMemo, useImperativeHandle, forwardRef } from "react"
import styles from "./Player.module.css"

export const Player = forwardRef(function Player({ file, onTimeUpdate }, ref) {
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
        mediaRef.current.play().catch(() => {})
      }
    }
  }), [])

  function handleTimeUpdate() {
    if (mediaRef.current) onTimeUpdate(mediaRef.current.currentTime)
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
        : <div className={styles.empty}>No file loaded</div>
      }
    </div>
  )
})

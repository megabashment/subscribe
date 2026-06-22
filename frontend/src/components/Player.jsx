import { useEffect, useRef } from "react"
import styles from "./Player.module.css"

export function Player({ file, cues, activeCueId, onTimeUpdate }) {
  const ref = useRef(null)

  const url = file ? URL.createObjectURL(file) : null

  useEffect(() => {
    return () => { if (url) URL.revokeObjectURL(url) }
  }, [url])

  function handleTimeUpdate() {
    if (!ref.current) return
    onTimeUpdate(ref.current.currentTime)
  }

  function seekTo(time) {
    if (ref.current) ref.current.currentTime = time
  }

  // expose seekTo via ref callback on the container
  useEffect(() => {
    if (ref.current) ref.current._seekTo = seekTo
  })

  const isVideo = file && file.type.startsWith("video/")
  const MediaEl = isVideo ? "video" : "audio"

  return (
    <div className={styles.player}>
      <MediaEl
        ref={ref}
        src={url}
        controls
        className={isVideo ? styles.video : styles.audio}
        onTimeUpdate={handleTimeUpdate}
      />
    </div>
  )
}

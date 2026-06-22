import { useState, useEffect } from 'react'
import {
  IconCpu,
  IconDeviceDesktop,
  IconServer,
  IconServerCog,
} from '@tabler/icons-react'
import styles from './StatsBar.module.css'

const API = 'http://localhost:8511'
const ICON_SIZE = 14

function Bar({ value, max = 100, warn = 80 }) {
  const pct = Math.min(100, Math.round((value / max) * 100))
  const hot = pct >= warn
  return (
    <div className={styles.bar}>
      <div
        className={`${styles.fill} ${hot ? styles.hot : ''}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}

function Stat({ icon, label, value, bar, barMax, barWarn }) {
  return (
    <div className={styles.stat}>
      <span className={styles.icon}>{icon}</span>
      <span className={styles.label}>{label}</span>
      <span className={styles.value}>{value}</span>
      {bar !== undefined && <Bar value={bar} max={barMax} warn={barWarn} />}
    </div>
  )
}

export function StatsBar({ active }) {
  const [data, setData] = useState(null)

  useEffect(() => {
    if (!active) { setData(null); return }

    // prime cpu_percent (first call always returns 0.0 in psutil)
    fetch(`${API}/stats`).catch(() => {})

    const id = setInterval(() => {
      fetch(`${API}/stats`)
        .then(r => r.json())
        .then(setData)
        .catch(() => {})
    }, 2000)

    return () => clearInterval(id)
  }, [active])

  if (!active || !data) return null

  const gpu = data.gpu

  return (
    <div className={styles.statsBar}>
      <Stat
        icon={<IconCpu size={ICON_SIZE} stroke={1.5} />}
        label="CPU"
        value={`${data.cpu_load}%`}
        bar={data.cpu_load}
        barWarn={85}
      />
      <Stat
        icon={<IconServer size={ICON_SIZE} stroke={1.5} />}
        label="RAM"
        value={`${data.ram_used_gb} / ${data.ram_total_gb} GB`}
        bar={data.ram_used_gb}
        barMax={data.ram_total_gb}
        barWarn={85}
      />
      {gpu && (
        <>
          <Stat
            icon={<IconDeviceDesktop size={ICON_SIZE} stroke={1.5} />}
            label="GPU"
            value={`${gpu.load}%`}
            bar={gpu.load}
            barWarn={95}
          />
          <Stat
            icon={<IconServerCog size={ICON_SIZE} stroke={1.5} />}
            label="VRAM"
            value={`${gpu.vram_used_mb} / ${gpu.vram_total_mb} MB`}
            bar={gpu.vram_used_mb}
            barMax={gpu.vram_total_mb}
            barWarn={90}
          />
        </>
      )}
    </div>
  )
}

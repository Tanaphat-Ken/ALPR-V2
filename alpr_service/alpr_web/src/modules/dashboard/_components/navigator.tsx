'use client'

import { usePathname } from 'next/navigation'

const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1)

const Navigator = () => {
  const path = usePathname()
  // parts = ['dashboard', 'upload', 'image'] (skip index 0 which is empty string before first /)
  const parts = path.split('/').filter(Boolean).slice(1) // remove 'dashboard' prefix handled separately

  return (
    <div style={{ marginBottom: 16 }}>
      <span style={{ opacity: 0.4 }}>Dashboard</span>
      {parts.map((part, index) => {
        const isLast = index === parts.length - 1
        return (
          <span key={part}>
            <span style={{ opacity: 0.4 }}> / </span>
            <span style={{ opacity: isLast ? 1 : 0.4, textTransform: 'capitalize' }}>
              {capitalize(part)}
            </span>
          </span>
        )
      })}
    </div>
  )
}

export default Navigator
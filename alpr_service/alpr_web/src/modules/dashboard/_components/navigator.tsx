'use client'

import { usePathname } from 'next/navigation'

const Navigator = () => {
  const path = usePathname()
  const pageName = path.split('/')[2]

  return (
    <div style={{ marginBottom: 16 }}>
      <span style={{ opacity: 0.4 }}>Dashboard / </span>
      <span style={{ textTransform: 'capitalize' }}>{ pageName ? pageName : 'home' }</span>
    </div>
  )
}

export default Navigator
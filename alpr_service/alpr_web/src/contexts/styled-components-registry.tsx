'use client'

import { useState, PropsWithChildren } from 'react'
import { useServerInsertedHTML } from 'next/navigation'
import { ServerStyleSheet, StyleSheetManager } from 'styled-components'
import { App as AntdApp } from 'antd'

export default function StyledComponentsRegistry({ children }: PropsWithChildren) {
  const [styledComponentsStyleSheet] = useState(() => new ServerStyleSheet())

  useServerInsertedHTML(() => {
    const styles = styledComponentsStyleSheet.getStyleElement()
    styledComponentsStyleSheet.instance.clearTag()
    return <>{styles}</>
  })

  if (typeof window !== 'undefined') return <AntdApp>{children}</AntdApp>

  return (
    <StyleSheetManager sheet={styledComponentsStyleSheet.instance}>
      <AntdApp>{children}</AntdApp>
    </StyleSheetManager>
  )
}
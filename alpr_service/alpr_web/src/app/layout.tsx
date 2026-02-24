import type { Metadata } from 'next'
import localFont from 'next/font/local'
import { Unbounded, IBM_Plex_Sans_Thai } from 'next/font/google'

import ReactQueryProvider from '@/contexts/react-query-provider'
import StyledComponentsRegistry from '@/contexts/styled-components-registry'
import ReduxStoreProvider from '@/contexts/redux-store'

const geistSans = localFont({
  src: './fonts/GeistVF.woff',
  variable: '--font-geist-sans',
  weight: '100 900',
})
const geistMono = localFont({
  src: './fonts/GeistMonoVF.woff',
  variable: '--font-geist-mono',
  weight: '100 900',
})

const unbounded = Unbounded({
  subsets: ['latin'],
  weight: ['400', '700'],
  variable: '--font-unbounded',
})

const ibmPlexSansThai = IBM_Plex_Sans_Thai({
  subsets: ['thai', 'latin'],
  weight: ['400', '600', '700'],
  variable: '--font-ibm-plex-sans-thai',
})

export const metadata: Metadata = {
  title: 'ALPR V2 - Automatic License Plate Recognition Service',
  description: 'Next-generation AI-powered ALPR service for Thai license plates. Fast, accurate, and easy to integrate.',
}

const RootLayout = ({ children }: Readonly<{ children: React.ReactNode }>) => {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable} ${unbounded.variable} ${ibmPlexSansThai.variable}`} style={{ padding: 0, margin: 0, fontFamily: 'var(--font-ibm-plex-sans-thai), IBM Plex Sans Thai, sans-serif' }}>
        <ReactQueryProvider>
          <ReduxStoreProvider>
            <StyledComponentsRegistry>
              {children}
            </StyledComponentsRegistry>
          </ReduxStoreProvider>
        </ReactQueryProvider>
      </body>
    </html>
  )
}

export default RootLayout
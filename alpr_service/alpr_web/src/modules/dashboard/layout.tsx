import { PropsWithChildren } from 'react'

import { Layout } from 'antd'

import DashboardHeader from './_components/dashboard-header'
import DashboardMenu from './_components/dashboard-menu'
import DashboardContent from './_components/dashboard-content'

const DashboardLayout = ({ children }: PropsWithChildren) => {
  return (
    <Layout style={{ height: '100vh', overflow: 'hidden' }}>
      <DashboardHeader />
      <Layout style={{ flex: 1, overflow: 'hidden' }}>
        <DashboardMenu />
        <DashboardContent>{children}</DashboardContent>
      </Layout>
    </Layout>
  )
}

export default DashboardLayout
import { PropsWithChildren } from 'react'

import { Layout } from 'antd'

import DashboardHeader from './_components/dashboard-header'
import DashboardMenu from './_components/dashboard-menu'
import DashboardContent from './_components/dashboard-content'

const DashboardLayout = ({ children }: PropsWithChildren) => {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <DashboardHeader />
      <Layout>
        <DashboardMenu />
        <DashboardContent>{children}</DashboardContent>
      </Layout>
    </Layout>
  )
}

export default DashboardLayout
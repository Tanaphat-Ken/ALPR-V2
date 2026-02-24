import { PropsWithChildren } from 'react'

import { Content } from 'antd/lib/layout/layout'

import Navigator from './navigator'
import ModalContainer from './modal-container'

const DashboardContent = ({ children }: PropsWithChildren) => {
  return (
    <div style={{ padding: '1rem', flex: 1, overflow: 'auto' }}>
      <ModalContainer />
      <Navigator />
      <Content>{children}</Content>
    </div>
  )
}

export default DashboardContent
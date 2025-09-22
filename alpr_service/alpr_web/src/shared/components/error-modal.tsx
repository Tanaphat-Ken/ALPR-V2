'use client'

import { useSelector, useDispatch } from 'react-redux'
import { Modal } from 'antd'
import { CloseCircleOutlined } from '@ant-design/icons'

import { RootState, AppDispatch } from '@/shared/store'
import { setModalErrorMsg } from '../store/dashboard/shared'

const ModalTitle = () => {
  return (
    <p style={{ margin: 0 }}>
      <CloseCircleOutlined 
        style={{ color: 'red', marginRight: 8 }} 
      />Sorry, something went wrong
    </p>
  )  
}

const ErrorModal = () => {
  const dispatch = useDispatch<AppDispatch>()
  const modalErrorMsg = useSelector((state: RootState) => state.sharedState.modalErrorMsg)

  const handleOk = () => dispatch(setModalErrorMsg(''))

  return (
    <Modal
      title={<ModalTitle />} 
      open={modalErrorMsg === '' ? false : true}
      onOk={handleOk}
    >
      <p>{modalErrorMsg}</p>
    </Modal>
  )
}

export default ErrorModal
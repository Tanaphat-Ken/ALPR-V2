'use client'

import { PropsWithChildren } from 'react'

import styled from 'styled-components'

const StyledTitle = styled.h2`
  margin-top: 0;
  font-size: 16px;
  font-weight: normal;
  opacity: 0.4;
`

const SectionTitle = ({ children }: PropsWithChildren) => {
  return (
    <StyledTitle>{children}</StyledTitle>
  )
}

export default SectionTitle
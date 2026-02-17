'use client'

import { useState } from 'react'
import { Button, Form, Input, Typography, message, Checkbox } from 'antd'
import { LockOutlined, MailOutlined } from '@ant-design/icons'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import styled from 'styled-components'
import { register } from '@/libs/auth'

const { Title, Text } = Typography

const AuthContainer = styled.div`
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f9fafb;
`

const TopNavBar = styled.div`
  background: #150E4B;
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 48px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

  @media (max-width: 768px) {
    padding: 0 20px;
  }
`

const NavLogo = styled.div`
  color: white;
  font-size: 24px;
  font-weight: 700;
`

const ContentWrapper = styled.div`
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
`

const AuthCard = styled.div`
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  padding: 48px;
  width: 100%;
  max-width: 450px;

  @media (max-width: 768px) {
    padding: 32px 24px;
  }
`

const LogoSection = styled.div`
  text-align: center;
  margin-bottom: 32px;
`

const Logo = styled.div`
  width: 64px;
  height: 64px;
  background: #150E4B;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  font-size: 32px;
  color: white;
  font-weight: bold;
`

const AuthTitle = styled(Title)`
  &.ant-typography {
    text-align: center;
    margin-bottom: 8px;
    color: #1f2937;
  }
`

const AuthSubtitle = styled(Text)`
  display: block;
  text-align: center;
  color: #6b7280;
  margin-bottom: 32px;
`

const StyledForm = styled(Form)`
  .ant-form-item {
    margin-bottom: 20px;
  }
`

const StyledInput = styled(Input)`
  height: 48px;
  border-radius: 8px;
  font-size: 16px;
  display: flex;
  align-items: center;

  .ant-input-prefix {
    margin-right: 12px;
  }
`

const StyledPasswordInput = styled(Input.Password)`
  height: 48px;
  border-radius: 8px;
  font-size: 16px;
  display: flex !important;
  align-items: center;

  .ant-input {
    height: 100%; 
  }

  .ant-input-prefix {
    margin-right: 12px;
  }
`

const SubmitButton = styled(Button)`
  width: 100%;
  height: 48px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  margin-top: 8px;
  background: #584AC7;
  border-color: #584AC7;

  &:hover {
    background: #4a3fb0 !important;
    border-color: #4a3fb0 !important;
  }
`

const DividerText = styled.div`
  text-align: center;
  margin: 24px 0;
  color: #6b7280;
  position: relative;

  &::before,
  &::after {
    content: '';
    position: absolute;
    top: 50%;
    width: 45%;
    height: 1px;
    background: #e5e7eb;
  }

  &::before {
    left: 0;
  }

  &::after {
    right: 0;
  }
`

const LinkText = styled.div`
  text-align: center;
  margin-top: 24px;
  color: #6b7280;

  a {
    color: #584AC7;
    font-weight: 600;
    text-decoration: none;
    margin-left: 4px;

    &:hover {
      color: #2563EB;
      text-decoration: underline;
    }
  }
`

const TermsText = styled.span`
  color: #6b7280;
  font-size: 14px;

  a {
    color: #584AC7;
    text-decoration: none;

    &:hover {
      color: #2563EB;
      text-decoration: underline;
    }
  }
`

type RegisterFormValues = {
  email: string
  password: string
  confirmPassword: string
  agree: boolean
}

const RegisterPage = () => {
  const [loading, setLoading] = useState(false)
  const router = useRouter()
  const [form] = Form.useForm()

  const onFinish = async (values: RegisterFormValues) => {
    setLoading(true)
    try {
      // Call actual register API
      await register({
        email: values.email,
        password: values.password
      })

      message.success('Registration successful! Please login.')
      router.push('/login')
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } }
      const errorMessage = err?.response?.data?.detail || 'Registration failed. Please try again.'
      message.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthContainer>
      <TopNavBar>
        <Link href="/" style={{ textDecoration: 'none' }}>
          <NavLogo>ALPR VER 2</NavLogo>
        </Link>
      </TopNavBar>
      <ContentWrapper>
        <AuthCard>
          <LogoSection>
            <Logo>A</Logo>
            <AuthTitle level={2}>Create Account</AuthTitle>
            <AuthSubtitle>Sign up for ALPR V2 and get started</AuthSubtitle>
          </LogoSection>

          <StyledForm
            form={form}
            name="register"
            onFinish={onFinish as (values: unknown) => void}
            autoComplete="off"
            layout="vertical"
          >
            <Form.Item
              name="email"
              rules={[
                { required: true, message: 'Please input your email!' },
                { type: 'email', message: 'Please enter a valid email!' }
              ]}
            >
              <StyledInput
                prefix={<MailOutlined style={{ color: '#9ca3af' }} />}
                placeholder="Email address"
                size="large"
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[
                { required: true, message: 'Please input your password!' },
                { min: 6, message: 'Password must be at least 6 characters!' }
              ]}
            >
              <StyledPasswordInput
                prefix={<LockOutlined style={{ color: '#9ca3af' }} />}
                placeholder="Password"
                size="large"
              />
            </Form.Item>

            <Form.Item
              name="confirmPassword"
              dependencies={['password']}
              rules={[
                { required: true, message: 'Please confirm your password!' },
                ({ getFieldValue }) => ({
                  validator(_, value) {
                    if (!value || getFieldValue('password') === value) {
                      return Promise.resolve()
                    }
                    return Promise.reject(new Error('Passwords do not match!'))
                  },
                }),
              ]}
            >
              <StyledPasswordInput
                prefix={<LockOutlined style={{ color: '#9ca3af' }} />}
                placeholder="Confirm password"
                size="large"
              />
            </Form.Item>

            <Form.Item
              name="agree"
              valuePropName="checked"
              rules={[
                {
                  validator: (_, value) =>
                    value ? Promise.resolve() : Promise.reject(new Error('Please accept the terms and conditions')),
                },
              ]}
            >
              <Checkbox>
                <TermsText>
                  I agree to the <Link href="/terms">Terms of Service</Link> and{' '}
                  <Link href="/privacy">Privacy Policy</Link>
                </TermsText>
              </Checkbox>
            </Form.Item>

            <Form.Item>
              <SubmitButton
                type="primary"
                htmlType="submit"
                loading={loading}
                size="large"
              >
                Create Account
              </SubmitButton>
            </Form.Item>
          </StyledForm>

          <DividerText>or</DividerText>

          <LinkText>
            Already have an account?
            <Link href="/login">Sign in</Link>
          </LinkText>

          <LinkText style={{ marginTop: 16 }}>
            <Link href="/">← Back to Home</Link>
          </LinkText>
        </AuthCard>
      </ContentWrapper>
    </AuthContainer>
  )
}

export default RegisterPage

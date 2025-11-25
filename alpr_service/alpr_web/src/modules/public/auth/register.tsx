'use client'

import { useState } from 'react'
import { Button, Form, Input, Typography, message, Checkbox } from 'antd'
import { LockOutlined, MailOutlined, UserOutlined } from '@ant-design/icons'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import styled from 'styled-components'
import { register } from '@/libs/auth'

const { Title, Text } = Typography

const AuthContainer = styled.div`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
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
`

const StyledPasswordInput = styled(Input.Password)`
  height: 48px;
  border-radius: 8px;
  font-size: 16px;

  .ant-input {
    height: 46px;
  }
`

const SubmitButton = styled(Button)`
  width: 100%;
  height: 48px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  margin-top: 8px;
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
    color: #667eea;
    font-weight: 600;
    text-decoration: none;
    margin-left: 4px;

    &:hover {
      color: #764ba2;
      text-decoration: underline;
    }
  }
`

const TermsText = styled.span`
  color: #6b7280;
  font-size: 14px;

  a {
    color: #667eea;
    text-decoration: none;

    &:hover {
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
      // TODO: Uncomment when backend is ready
      // await register({
      //   email: values.email,
      //   password: values.password
      // })

      // Mock success for now
      message.success('Registration successful! Please login. (Mock)')
      // eslint-disable-next-line no-console
      console.log('Register values:', { email: values.email })
      router.push('/login')
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } }
      const errorMessage = err.response?.data?.detail || 'Registration failed. Please try again.'
      message.error(errorMessage)
      // eslint-disable-next-line no-console
      console.error('Register error:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthContainer>
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
            name="name"
            rules={[
              { required: true, message: 'Please input your name!' },
              { min: 2, message: 'Name must be at least 2 characters!' }
            ]}
          >
            <StyledInput
              prefix={<UserOutlined style={{ color: '#9ca3af' }} />}
              placeholder="Full name"
              size="large"
            />
          </Form.Item>

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
    </AuthContainer>
  )
}

export default RegisterPage

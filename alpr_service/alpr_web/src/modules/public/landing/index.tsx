'use client'

import { Button, Card, Col, Row, Typography } from 'antd'
import {
  CameraOutlined,
  CloudUploadOutlined,
  DashboardOutlined,
  FastForwardOutlined,
  LockOutlined,
  RocketOutlined,
  SafetyOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import Link from 'next/link'
import styled from 'styled-components'

const { Title, Paragraph } = Typography

const LandingContainer = styled.div`
  min-height: 100vh;
  background: #f9fafb;
`

const TopNavBar = styled.div`
  background: #150E4B;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
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
  display: flex;
  align-items: center;
  gap: 12px;
`

const NavButtons = styled.div`
  display: flex;
  gap: 12px;
`

const HeroSection = styled.section`
  padding: 100px 20px 80px;
  text-align: center;
  max-width: 1200px;
  margin: 0 auto;
`

const HeroTitle = styled(Title)`
  &.ant-typography {
    color: #1f2937 !important;
    font-size: 3.5rem;
    font-weight: 800;
    margin-bottom: 24px;

    @media (max-width: 768px) {
      font-size: 2.5rem;
    }
  }
`

const HeroSubtitle = styled(Paragraph)`
  &.ant-typography {
    color: #6b7280;
    font-size: 1.5rem;
    margin-bottom: 40px;
    font-weight: 400;

    @media (max-width: 768px) {
      font-size: 1.2rem;
    }
  }
`

const CTAButton = styled(Button)`
  height: 48px;
  font-size: 16px;
  padding: 0 32px;
  border-radius: 8px;
  margin: 0 8px;
  font-weight: 600;
  transition: all 0.3s ease;

  &.primary-btn {
    background: #584AC7;
    border-color: #584AC7;
    color: white;

    &:hover {
      background: #4a3fb0 !important;
      border-color: #4a3fb0 !important;
    }
  }

  &.secondary-btn {
    background: transparent;
    border: 2px solid #584AC7;
    color: #584AC7;

    &:hover {
      background: #584AC7 !important;
      color: white !important;
    }
  }

  @media (max-width: 768px) {
    margin: 8px 0;
    width: 100%;
  }
`

const NavButton = styled(Button)`
  height: 40px;
  border-radius: 6px;
  font-weight: 500;

  &.nav-login {
    background: transparent;
    border: 1px solid white;
    color: white;

    &:hover {
      background: rgba(255, 255, 255, 0.1) !important;
      border-color: white !important;
    }
  }

  &.nav-signup {
    background: #584AC7;
    border-color: #584AC7;
    color: white;

    &:hover {
      background: #4a3fb0 !important;
      border-color: #4a3fb0 !important;
    }
  }
`

const FeaturesSection = styled.section`
  padding: 80px 20px;
  background: white;
`

const FeaturesContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
`

const SectionTitle = styled(Title)`
  &.ant-typography {
    text-align: center;
    margin-bottom: 60px;
    font-size: 2.5rem;
    color: #1f2937;
  }
`

const FeatureCard = styled(Card)`
  height: 100%;
  border-radius: 16px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
  transition: all 0.3s ease;
  border: none;

  &:hover {
    transform: translateY(-8px);
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
  }

  .ant-card-body {
    padding: 32px;
  }
`

const FeatureIcon = styled.div`
  font-size: 48px;
  margin-bottom: 20px;
  color: #584AC7;
`

const FeatureTitle = styled(Title)`
  &.ant-typography {
    margin-bottom: 12px;
    color: #1f2937;
  }
`

const FeatureDescription = styled(Paragraph)`
  &.ant-typography {
    color: #6b7280;
    font-size: 16px;
    margin-bottom: 0;
  }
`

const StatsSection = styled.section`
  padding: 80px 20px;
  background: #150E4B;
  color: white;
`

const StatCard = styled.div`
  text-align: center;
  padding: 32px;
`

const StatNumber = styled.div`
  font-size: 3rem;
  font-weight: 800;
  margin-bottom: 8px;
  color: white;
`

const StatLabel = styled.div`
  font-size: 1.1rem;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 300;
`

const Footer = styled.footer`
  background: #0f0a3a;
  color: white;
  padding: 40px 20px;
  text-align: center;
`

const FooterText = styled(Paragraph)`
  &.ant-typography {
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 0;
  }
`

const LandingPage = () => {
  const features = [
    {
      icon: <ThunderboltOutlined />,
      title: 'Lightning Fast',
      description: 'Advanced AI model processes license plates in milliseconds with high accuracy',
    },
    {
      icon: <CameraOutlined />,
      title: 'Multi-Format Support',
      description: 'Supports images and video streams from various sources and formats',
    },
    {
      icon: <SafetyOutlined />,
      title: 'High Accuracy',
      description: 'State-of-the-art TrOCR model trained specifically for Thai license plates',
    },
    {
      icon: <CloudUploadOutlined />,
      title: 'Easy Integration',
      description: 'RESTful API and WebSocket support for seamless integration into your system',
    },
    {
      icon: <LockOutlined />,
      title: 'Secure & Reliable',
      description: 'Token-based authentication and encrypted data transmission',
    },
    {
      icon: <DashboardOutlined />,
      title: 'Real-time Dashboard',
      description: 'Monitor and manage your recognition requests with intuitive dashboard',
    },
  ]

  return (
    <LandingContainer>
      {/* Top Navigation Bar */}
      <TopNavBar>
        <NavLogo>
          <span>ALPR VER 2</span>
        </NavLogo>
        <NavButtons>
          <Link href="/login">
            <NavButton className="nav-login">
              Login
            </NavButton>
          </Link>
          <Link href="/register">
            <NavButton className="nav-signup">
              Sign Up
            </NavButton>
          </Link>
        </NavButtons>
      </TopNavBar>

      {/* Hero Section */}
      <HeroSection>
        <HeroTitle level={1}>
          Automatic License Plate Recognition
        </HeroTitle>
        <HeroSubtitle>
          Next-generation AI-powered ALPR service for Thai license plates.
          Fast, accurate, and easy to integrate.
        </HeroSubtitle>
        <div>
          <Link href="/login">
            <CTAButton className="primary-btn" icon={<RocketOutlined />}>
              Get Started
            </CTAButton>
          </Link>
          <Link href="/register">
            <CTAButton className="secondary-btn" icon={<FastForwardOutlined />}>
              Sign Up Free
            </CTAButton>
          </Link>
        </div>
      </HeroSection>

      {/* Features Section */}
      <FeaturesSection>
        <FeaturesContainer>
          <SectionTitle level={2}>
            Why Choose ALPR V2?
          </SectionTitle>
          <Row gutter={[32, 32]}>
            {features.map((feature, index) => (
              <Col xs={24} sm={12} lg={8} key={index}>
                <FeatureCard>
                  <FeatureIcon>{feature.icon}</FeatureIcon>
                  <FeatureTitle level={4}>{feature.title}</FeatureTitle>
                  <FeatureDescription>{feature.description}</FeatureDescription>
                </FeatureCard>
              </Col>
            ))}
          </Row>
        </FeaturesContainer>
      </FeaturesSection>

      {/* Stats Section */}
      <StatsSection>
        <FeaturesContainer>
          <Row gutter={[32, 32]}>
            <Col xs={24} sm={8}>
              <StatCard>
                <StatNumber>97%</StatNumber>
                <StatLabel>Recognition Accuracy</StatLabel>
              </StatCard>
            </Col>
            <Col xs={24} sm={8}>
              <StatCard>
                <StatNumber>&lt;100ms</StatNumber>
                <StatLabel>Average Processing Time</StatLabel>
              </StatCard>
            </Col>
            <Col xs={24} sm={8}>
              <StatCard>
                <StatNumber>24/7</StatNumber>
                <StatLabel>Service Availability</StatLabel>
              </StatCard>
            </Col>
          </Row>
        </FeaturesContainer>
      </StatsSection>

      {/* Footer */}
      <Footer>
        <FooterText>
          © 2025 ALPR V2 - Automatic License Plate Recognition Service. All rights reserved.
        </FooterText>
      </Footer>
    </LandingContainer>
  )
}

export default LandingPage

'use client'

import styled from 'styled-components'
import { useSelector } from 'react-redux'
import { Line } from 'react-chartjs-2'
import { 
  Chart as ChartJS, 
  ChartOptions,
  CategoryScale, 
  LinearScale, 
  PointElement, 
  LineElement, 
  Title, 
  Tooltip, 
  Legend 
} from 'chart.js'

import SectionTitle from '../../../../shared/components/section-title'
import { useTokenUsage } from '@/api/dashboard/token/hooks'
import { RootState } from '@/shared/store'
import { TokenUsageType } from '@/shared/types/token'

const colorMap = [
  '#F59E0B',
  '#14B8A6',
  '#8B5CF6',
  '#78716C',
  '#F43F5E'
]

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

const chartOptions: ChartOptions<'line'> = {
  responsive: true,
  plugins: {
    legend: {
      position: 'top',
      labels: {
        usePointStyle: true,
      }
    },
  },
  interaction: {
    mode: 'index',
    intersect: false,
  },
  scales: {
    x: {
      type: 'category',
      title: {
        display: true,
        text: 'Hour of the Day'
      }
    },
    y: {
      title: {
        display: true,
        text: 'Usage Per Hour'
      },
      beginAtZero: true
    }
  }
}

const getHoursAxis = () => {
  const currentTime = new Date()
  return Array.from({ length: 24 }, (_, i) => {
    const hour = new Date(currentTime)
    hour.setHours(currentTime.getHours() - i)
    return `${hour.getHours()}:${hour.getMinutes().toString().padStart(2, '0')}`
  }).reverse()
}

const LineContainer = styled.div`
  background-color: white;
  padding: 16px; 
  border-radius: 10px;
  border: '1px solid #00000013';
  max-width: 1280px;
`

const DotChart = ({ tokenList }: { tokenList: TokenUsageType[] }) => {
  const hours = getHoursAxis()

  const datasets = tokenList.map((item, index) => ({
    label: item.token_key,
    data: item.usage_per_hour,
    fill: false,
    borderColor: colorMap[index],
    pointBackgroundColor: '#FFFFFF',
    tension: 0.1,
  }))

  const chartData = {
    labels: hours,
    datasets: datasets
  }

  return (
    <LineContainer>
      <Line data={chartData} options={chartOptions} />
    </LineContainer>
  )
}

const TokensGraph = () => {
  const activeService = useSelector((state: RootState) => state.homePageSlice.activeService)
  const userId = useSelector((state: RootState) => state.user.userId)
  const { data: tokenUsageList } = useTokenUsage(userId, activeService)

  return (
    <div style={{ marginTop: 16 }}>
      <SectionTitle>Tokens Usage</SectionTitle>
      <DotChart tokenList={tokenUsageList ? tokenUsageList : []} />
    </div>
  )
}

export default TokensGraph
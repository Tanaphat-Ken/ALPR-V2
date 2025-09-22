import WelcomeBanner from './_components/welcom-banner'
import SubscriptionList from './_components/subscirption-list'
import TokensGraph from './_components/tokens-graph'

const DashboardHome = () => {
  return (
    <div>
      <WelcomeBanner />
      <SubscriptionList />
      <TokensGraph />
    </div>
  )
}

export default DashboardHome
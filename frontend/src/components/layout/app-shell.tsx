import { useLayout } from '@/hooks/use-media-query'
import { useTripPlanner } from '@/hooks/use-trip-planner'
import { ColumnsLayout } from './columns-layout'
import { StackedLayout } from './stacked-layout'

/**
 * The planner, laid out for the device (ADR-0013): columns beside the map on laptops and
 * sideways phones, the map above a panel on phones and tablets held upright. The trip
 * lives here, so it survives a phone rotating from one layout to the other.
 */
export function AppShell() {
  const layout = useLayout()
  const planner = useTripPlanner()
  return layout === 'stacked' ? (
    <StackedLayout planner={planner} />
  ) : (
    <ColumnsLayout planner={planner} variant={layout} />
  )
}

import { useEffect, useState } from 'react'

const MOBILE_BREAKPOINT_QUERY = '(max-width: 767px)' // Tailwind's `md` breakpoint

/** True below Tailwind's `md` breakpoint. Used where a layout needs to
 * switch structure (not just spacing/sizing) between mobile and desktop --
 * e.g. showing one drill-down column at a time instead of three side by side. */
export function useIsMobile(): boolean {
  const [isMobile, setIsMobile] = useState(
    () => typeof window !== 'undefined' && window.matchMedia(MOBILE_BREAKPOINT_QUERY).matches,
  )

  useEffect(() => {
    const mql = window.matchMedia(MOBILE_BREAKPOINT_QUERY)
    const onChange = () => setIsMobile(mql.matches)
    mql.addEventListener('change', onChange)
    return () => mql.removeEventListener('change', onChange)
  }, [])

  return isMobile
}

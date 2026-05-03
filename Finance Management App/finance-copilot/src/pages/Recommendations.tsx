import { useAppStore } from '../stores/appStore'
import { RecommendationCard } from '../components/cards/RecommendationCard'
import { MOCK_RECOMMENDATIONS } from '../lib/mockData'
import { useEffect, useRef } from 'react'

export function Recommendations() {
  const { recommendations, setRecommendations, acceptRecommendation, snoozeRecommendation, dismissRecommendation } = useAppStore()
  const seededMockRef = useRef(false)

  useEffect(() => {
    if (recommendations.length > 0 || seededMockRef.current) return
    seededMockRef.current = true
    setRecommendations(MOCK_RECOMMENDATIONS)
  }, [recommendations.length, setRecommendations])

  const pending = recommendations.filter(r => r.status === 'pending')
  const actioned = recommendations.filter(r => r.status !== 'pending')

  return (
    <div className="h-full overflow-y-auto p-6">
      {pending.length > 0 && (
        <>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-white">Active Recommendations</h2>
            <span className="text-xs text-navy-400">{pending.length} pending</span>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4 mb-8">
            {pending.map(rec => (
              <RecommendationCard
                key={rec.id}
                rec={rec}
                onAccept={acceptRecommendation}
                onSnooze={snoozeRecommendation}
                onDismiss={dismissRecommendation}
              />
            ))}
          </div>
        </>
      )}

      {actioned.length > 0 && (
        <>
          <h2 className="text-sm font-semibold text-navy-400 mb-4">Actioned</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
            {actioned.map(rec => (
              <RecommendationCard
                key={rec.id}
                rec={rec}
                onAccept={acceptRecommendation}
                onSnooze={snoozeRecommendation}
                onDismiss={dismissRecommendation}
              />
            ))}
          </div>
        </>
      )}

      {recommendations.length === 0 && (
        <div className="flex flex-col items-center justify-center h-64 text-center">
          <p className="text-4xl mb-4">💡</p>
          <p className="text-sm font-medium text-white mb-1">No recommendations yet</p>
          <p className="text-xs text-navy-400">Connect your bank account to generate personalised insights.</p>
        </div>
      )}
    </div>
  )
}

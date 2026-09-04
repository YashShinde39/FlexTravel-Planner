import { useEffect, useState } from 'react'

function App() {
  const [itineraries, setItineraries] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const loadItineraries = async () => {
      try {
        const response = await fetch('/api/itineraries/')
        if (!response.ok) {
          throw new Error('Unable to fetch travel options.')
        }

        const data = await response.json()
        setItineraries(data.itineraries || [])
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    loadItineraries()
  }, [])

  return (
    <main className="min-h-screen bg-slate-100 px-4 py-10">
      <div className="mx-auto max-w-6xl">
        <h1 className="mb-2 text-center text-3xl font-bold text-slate-900 md:text-4xl">
          FlexTravel Planner
        </h1>
        <p className="mb-8 text-center text-slate-600">
          Compare curated itinerary options and choose your best fit.
        </p>

        {loading && <p className="text-center text-slate-600">Loading travel options...</p>}
        {error && <p className="text-center text-red-600">{error}</p>}

        {!loading && !error && (
          <section className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {itineraries.map((option) => (
              <article
                key={option.id}
                className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200"
              >
                <h2 className="text-xl font-semibold text-slate-900">{option.title}</h2>
                <p className="mt-2 text-sm text-slate-600">Duration: {option.duration_days} days</p>
                <p className="text-sm font-medium text-slate-700">Budget: ${option.budget_usd}</p>
                <ul className="mt-4 list-disc space-y-1 pl-5 text-sm text-slate-600">
                  {option.highlights.map((highlight) => (
                    <li key={highlight}>{highlight}</li>
                  ))}
                </ul>
              </article>
            ))}
          </section>
        )}
      </div>
    </main>
  )
}

export default App

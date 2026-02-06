import { createFileRoute } from '@tanstack/react-router'
import { Search, Loader2 } from 'lucide-react'
import { useState } from 'react'

export const Route = createFileRoute('/search')({
  component: SearchFlashcardsPage,
})

interface Flashcard {
  id: string
  question: string
  answer: string
  deck_id: string
}

function SearchFlashcardsPage() {
  const [topic, setTopic] = useState('')
  const [flashcards, setFlashcards] = useState<Flashcard[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasSearched, setHasSearched] = useState(false)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!topic.trim()) return

    setIsLoading(true)
    setError(null)
    setHasSearched(true)

    try {
      const response = await fetch(
        `http://localhost:8000/cards/topic/${encodeURIComponent(topic)}`,
        {
          credentials: 'include',
        }
      )

      if (!response.ok) {
        throw new Error('Failed to search flashcards')
      }

      const data = await response.json()
      setFlashcards(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-linear-to-b from-slate-900 via-slate-800 to-slate-900 py-16 px-4">
      <div className="container mx-auto max-w-4xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="avatar placeholder mb-4">
            <div className="bg-linear-to-br from-green-500 to-emerald-500 text-white w-16 rounded-full">
              <Search className="w-8 h-8" />
            </div>
          </div>
          <h1 className="text-4xl font-bold text-white mb-2">
            Search Flashcards
          </h1>
          <p className="text-gray-400">
            Find relevant flashcards using AI-powered semantic search
          </p>
        </div>

        {/* Search Form */}
        <div className="card bg-base-200 border-2 border-green-500/20 shadow-xl mb-8">
          <div className="card-body">
            <form onSubmit={handleSearch} className="flex gap-2">
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Enter a topic or keyword..."
                className="input input-bordered input-success flex-1"
                disabled={isLoading}
              />
              <button
                type="submit"
                className="btn btn-success"
                disabled={!topic.trim() || isLoading}
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Search className="w-5 h-5" />
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="alert alert-error mb-8">
            <span>{error}</span>
          </div>
        )}

        {/* Results */}
        {hasSearched && !isLoading && (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-white mb-4">
              {flashcards.length > 0
                ? `Found ${flashcards.length} flashcard${flashcards.length !== 1 ? 's' : ''}`
                : 'No flashcards found'}
            </h2>

            {flashcards.map((card, index) => (
              <div
                key={card.id}
                className="card bg-base-200 border border-green-500/20 hover:border-green-500/40 transition-all"
              >
                <div className="card-body">
                  <div className="flex items-start gap-4">
                    <div className="badge badge-success badge-lg">{index + 1}</div>
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-white mb-2">
                        {card.question}
                      </h3>
                      <div className="divider my-2"></div>
                      <p className="text-base-content/70">{card.answer}</p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="flex justify-center items-center py-16">
            <Loader2 className="w-12 h-12 animate-spin text-green-500" />
          </div>
        )}
      </div>
    </div>
  )
}
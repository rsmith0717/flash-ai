import { createFileRoute } from '@tanstack/react-router'
import { Search, Loader2, AlertCircle } from 'lucide-react'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '@/context/AuthContext'

export const Route = createFileRoute('/search')({
  component: SearchFlashcardsPage,
})

interface Flashcard {
  id: string
  question: string
  answer: string
  deck_id: string
}

async function searchFlashcards(topic: string): Promise<Flashcard[]> {
  // Get the access token from localStorage
  const token = localStorage.getItem('token')
  
  if (!token) {
    throw new Error('No authentication token found. Please log in.')
  }

  const response = await fetch(
    `http://localhost:8000/cards/topic/${encodeURIComponent(topic)}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      credentials: 'include',
    }
  )

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Search failed' }))
    throw new Error(errorData.detail || `Server error: ${response.status}`)
  }

  return response.json()
}

function SearchFlashcardsPage() {
  const [topic, setTopic] = useState('')
  const [searchTopic, setSearchTopic] = useState('')
  const { user } = useAuth()

  // Use TanStack Query with enabled condition
  const { data: flashcards = [], isLoading, error, refetch } = useQuery({
    queryKey: ['flashcards', 'search', searchTopic],
    queryFn: () => searchFlashcards(searchTopic),
    enabled: !!searchTopic && !!user, // Only run query if we have a search topic and user is logged in
    retry: 1,
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (!topic.trim()) return
    
    // Update the search topic which will trigger the query
    setSearchTopic(topic.trim())
  }

  const hasSearched = !!searchTopic

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

        {/* Not Logged In Warning */}
        {!user && (
          <div className="alert alert-warning mb-8">
            <AlertCircle className="w-5 h-5" />
            <span>Please log in to search flashcards</span>
          </div>
        )}

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
                disabled={isLoading || !user}
              />
              <button
                type="submit"
                className="btn btn-success"
                disabled={!topic.trim() || isLoading || !user}
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Search className="w-5 h-5" />
                )}
              </button>
            </form>
            {hasSearched && (
              <div className="mt-2 text-sm text-base-content/70">
                Searching for: <span className="font-semibold text-success">"{searchTopic}"</span>
              </div>
            )}
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="alert alert-error mb-8">
            <AlertCircle className="w-5 h-5" />
            <span>{error instanceof Error ? error.message : 'Search failed'}</span>
          </div>
        )}

        {/* Results */}
        {hasSearched && !isLoading && !error && (
          <div className="space-y-4">
            <h2 className="text-2xl font-bold text-white mb-4">
              {flashcards.length > 0
                ? `Found ${flashcards.length} flashcard${flashcards.length !== 1 ? 's' : ''}`
                : 'No flashcards found'}
            </h2>

            {flashcards.length === 0 && (
              <div className="alert alert-info">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  className="stroke-current shrink-0 w-6 h-6"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <span>Try searching for a different topic or create some flashcards first!</span>
              </div>
            )}

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
          <div className="flex flex-col justify-center items-center py-16">
            <Loader2 className="w-12 h-12 animate-spin text-green-500 mb-4" />
            <p className="text-gray-400">Searching flashcards...</p>
          </div>
        )}
      </div>
    </div>
  )
}
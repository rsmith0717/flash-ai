import { createFileRoute } from '@tanstack/react-router'
import {
  FileJson,
  FileText,
  Search,
  MessageSquare,
  Sparkles,
} from 'lucide-react'
import FeatureCard from '@/components/FeatureCard'

export const Route = createFileRoute('/')({ component: App })

function App() {
  const colorSchemes = {
    cyan: {
      gradient: 'bg-gradient-to-br from-cyan-500 to-blue-500',
      iconBg: 'bg-cyan-500/20',
      iconText: 'text-cyan-400',
      border: 'hover:border-cyan-500',
      shadow: 'hover:shadow-cyan-500/20',
      btnClass: 'btn-primary',
    },
    purple: {
      gradient: 'bg-gradient-to-br from-purple-500 to-pink-500',
      iconBg: 'bg-purple-500/20',
      iconText: 'text-purple-400',
      border: 'hover:border-purple-500',
      shadow: 'hover:shadow-purple-500/20',
      btnClass: 'btn-secondary',
    },
    green: {
      gradient: 'bg-gradient-to-br from-green-500 to-emerald-500',
      iconBg: 'bg-green-500/20',
      iconText: 'text-green-400',
      border: 'hover:border-green-500',
      shadow: 'hover:shadow-green-500/20',
      btnClass: 'btn-success',
    },
    pink: {
      gradient: 'bg-gradient-to-br from-pink-500 to-rose-500',
      iconBg: 'bg-pink-500/20',
      iconText: 'text-pink-400',
      border: 'hover:border-pink-500',
      shadow: 'hover:shadow-pink-500/20',
      btnClass: 'btn-accent',
    },
  }

  return (
    <div className="min-h-screen bg-linear-to-b from-slate-900 via-slate-800 to-slate-900">
      <div className="container mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="avatar placeholder mb-6">
            <div className="bg-linear-to-br from-cyan-500 to-purple-500 text-white w-20 rounded-full">
              <Sparkles className="w-10 h-10" />
            </div>
          </div>
          <h1 className="text-5xl font-bold text-white mb-4 bg-linear-to-r from-cyan-400 via-purple-400 to-pink-400 bg-clip-text">
            Flash AI
          </h1>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            AI-powered flashcard learning platform with intelligent study features
          </p>
        </div>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-5xl mx-auto">
          <FeatureCard
            to="/upload-json"
            icon={FileJson}
            title="Upload JSON Deck"
            description="Create a new flashcard deck by uploading a JSON file with questions and answers"
            colorScheme={colorSchemes.cyan}
          />

          <FeatureCard
            to="/upload-text"
            icon={FileText}
            title="Upload Text Document"
            description="Create flashcards from a .txt document and let AI process the content"
            colorScheme={colorSchemes.purple}
          />

          <FeatureCard
            to="/search"
            icon={Search}
            title="Search Flashcards"
            description="Find relevant flashcards by topic using AI-powered semantic search"
            colorScheme={colorSchemes.green}
          />

          <FeatureCard
            to="/study"
            icon={MessageSquare}
            title="AI Study Assistant"
            description="Chat with an AI tutor that helps you study using your flashcard content"
            colorScheme={colorSchemes.pink}
          />
        </div>

        {/* Footer */}
        <div className="mt-16 text-center">
          <div className="divider"></div>
          <p className="text-gray-500 text-sm">
            All features are powered by AI embeddings and semantic search
          </p>
        </div>
      </div>
    </div>
  )
}
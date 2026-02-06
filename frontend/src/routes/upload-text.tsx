import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { FileText, Upload, AlertCircle, CheckCircle } from 'lucide-react'
import { useState } from 'react'
import { useAuth } from '@/context/AuthContext'

export const Route = createFileRoute('/upload-text')({
  component: TextUploadPage,
})

function TextUploadPage() {
  const [file, setFile] = useState<File | null>(null)
  const [deckName, setDeckName] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const { user } = useAuth()
  const navigate = useNavigate()

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.txt')) {
        setError('Please select a .txt file')
        return
      }
      setFile(selectedFile)
      setError(null)
      setSuccess(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file || !deckName || !user) return

    setIsLoading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('deck_name', deckName)

      // TODO: This endpoint needs to be created in the backend
      const response = await fetch('http://localhost:8000/cards/deck/upload/text', {
        method: 'POST',
        body: formData,
        credentials: 'include',
      })

      if (!response.ok) {
        throw new Error('Failed to upload and process document')
      }

      setSuccess(true)
      setTimeout(() => navigate({ to: '/' }), 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-linear-to-b from-slate-900 via-slate-800 to-slate-900 py-16 px-4">
      <div className="container mx-auto max-w-2xl">
        <div className="card bg-base-200 border-2 border-purple-500/20 shadow-xl">
          <div className="card-body">
            {/* Header */}
            <div className="text-center mb-6">
              <div className="avatar placeholder mb-4">
                <div className="bg-linear-to-br from-purple-500 to-pink-500 text-white w-16 rounded-full">
                  <FileText className="w-8 h-8" />
                </div>
              </div>
              <h1 className="card-title text-3xl justify-center mb-2">
                Upload Text Document
              </h1>
              <p className="text-base-content/70">
                AI will process your document and create flashcards
              </p>
            </div>

            {/* Error Alert */}
            {error && (
              <div className="alert alert-error mb-4">
                <AlertCircle className="w-5 h-5" />
                <span>{error}</span>
              </div>
            )}

            {/* Success Alert */}
            {success && (
              <div className="alert alert-success mb-4">
                <CheckCircle className="w-5 h-5" />
                <span>Document processed successfully! Redirecting...</span>
              </div>
            )}

            {/* Upload Form */}
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="form-control">
                <label className="label">
                  <span className="label-text">Deck Name</span>
                </label>
                <input
                  type="text"
                  value={deckName}
                  onChange={(e) => setDeckName(e.target.value)}
                  placeholder="e.g., Biology Chapter 3"
                  className="input input-bordered input-secondary w-full"
                  disabled={isLoading}
                  required
                />
              </div>

              <div className="form-control">
                <label className="label">
                  <span className="label-text">Text Document</span>
                </label>
                <input
                  type="file"
                  accept=".txt"
                  onChange={handleFileChange}
                  className="file-input file-input-bordered file-input-secondary w-full"
                  disabled={isLoading}
                />
                <label className="label">
                  <span className="label-text-alt">
                    Upload a .txt file and AI will extract flashcards
                  </span>
                </label>
              </div>

              <div className="card-actions justify-end">
                <button
                  type="button"
                  onClick={() => navigate({ to: '/' })}
                  className="btn btn-ghost"
                  disabled={isLoading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-secondary"
                  disabled={!file || !deckName || isLoading}
                >
                  {isLoading ? (
                    <>
                      <span className="loading loading-spinner"></span>
                      Processing...
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4" />
                      Process Document
                    </>
                  )}
                </button>
              </div>
            </form>

            {/* Info Box */}
            <div className="alert alert-info mt-6">
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
              <span>
                Our AI will analyze your document and automatically generate
                question-answer pairs for effective studying.
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
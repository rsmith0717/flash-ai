import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { FileJson, Upload, AlertCircle, CheckCircle } from 'lucide-react'
import { useState } from 'react'
import { useAuth } from '@/context/AuthContext'

export const Route = createFileRoute('/upload-json')({
  component: JsonUploadPage,
})

function JsonUploadPage() {
  const [file, setFile] = useState<File | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const { user } = useAuth()
  const navigate = useNavigate()

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.json')) {
        setError('Please select a JSON file')
        return
      }
      setFile(selectedFile)
      setError(null)
      setSuccess(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file || !user) return

    setIsLoading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('http://localhost:8000/cards/deck/upload', {
        method: 'POST',
        body: formData,
        credentials: 'include',
      })

      if (!response.ok) {
        throw new Error('Failed to upload deck')
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
        <div className="card bg-base-200 border-2 border-cyan-500/20 shadow-xl">
          <div className="card-body">
            {/* Header */}
            <div className="text-center mb-6">
              <div className="avatar placeholder mb-4">
                <div className="bg-linear-to-br from-cyan-500 to-blue-500 text-white w-16 rounded-full">
                  <FileJson className="w-8 h-8" />
                </div>
              </div>
              <h1 className="card-title text-3xl justify-center mb-2">
                Upload JSON Deck
              </h1>
              <p className="text-base-content/70">
                Upload a JSON file with flashcard questions and answers
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
                <span>Deck uploaded successfully! Redirecting...</span>
              </div>
            )}

            {/* Upload Form */}
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="form-control">
                <label className="label">
                  <span className="label-text">JSON File</span>
                </label>
                <input
                  type="file"
                  accept=".json"
                  onChange={handleFileChange}
                  className="file-input file-input-bordered file-input-primary w-full"
                  disabled={isLoading}
                />
                <label className="label">
                  <span className="label-text-alt">
                    Expected format: {"{"}"deck_name": "...", "flashcards": [...]
                    {"}"}
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
                  className="btn btn-primary"
                  disabled={!file || isLoading}
                >
                  {isLoading ? (
                    <>
                      <span className="loading loading-spinner"></span>
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4" />
                      Upload Deck
                    </>
                  )}
                </button>
              </div>
            </form>

            {/* Example Format */}
            <div className="divider">Example Format</div>
            <div className="mockup-code text-sm">
              <pre data-prefix="1">
                <code>{'{'}</code>
              </pre>
              <pre data-prefix="2">
                <code>  "deck_name": "History Quiz",</code>
              </pre>
              <pre data-prefix="3">
                <code>  "flashcards": [</code>
              </pre>
              <pre data-prefix="4">
                <code>    {'{'}"question": "Q1", "answer": "A1"{'}'},</code>
              </pre>
              <pre data-prefix="5">
                <code>    {'{'}"question": "Q2", "answer": "A2"{'}'}</code>
              </pre>
              <pre data-prefix="6">
                <code>  ]</code>
              </pre>
              <pre data-prefix="7">
                <code>{'}'}</code>
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
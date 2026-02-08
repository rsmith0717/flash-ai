import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { FileJson, Upload, AlertCircle, CheckCircle } from 'lucide-react'
import { useState } from 'react'
import { useAuth } from '@/context/AuthContext'
import { useMutation } from '@tanstack/react-query'

export const Route = createFileRoute('/upload-json')({
  component: JsonUploadPage,
})

interface UploadDeckResponse {
  id: string
  deck_name: string
  flashcards: Array<{
    id: string
    question: string
    answer: string
  }>
}

async function uploadDeckFile(file: File): Promise<UploadDeckResponse> {
  const token = localStorage.getItem('access_token')
  
  if (!token) {
    throw new Error('No authentication token found. Please log in.')
  }

  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch('http://localhost:8000/cards/deck/upload', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
    credentials: 'include',
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }))
    throw new Error(errorData.detail || `Server error: ${response.status}`)
  }

  return response.json()
}

function JsonUploadPage() {
  const [file, setFile] = useState<File | null>(null)
  const { user } = useAuth()
  const navigate = useNavigate()

  const uploadMutation = useMutation({
    mutationFn: uploadDeckFile,
    onSuccess: (data) => {
      console.log('Upload successful:', data)
      setTimeout(() => navigate({ to: '/' }), 2000)
    },
    onError: (error: Error) => {
      console.error('Upload error:', error)
    },
  })

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      if (!selectedFile.name.endsWith('.json')) {
        setFile(null)
        return
      }
      setFile(selectedFile)
      uploadMutation.reset()
    }
  }

  const handleSubmit = async (e: React.SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault()
    
    if (!user) {
      return
    }

    if (!file) {
      return
    }

    uploadMutation.mutate(file)
  }

  const isLoading = uploadMutation.isPending
  const error = uploadMutation.error?.message || null
  const success = uploadMutation.isSuccess

  return (
    <div className="min-h-screen bg-base-100 py-16 px-4">
      <div className="container mx-auto max-w-2xl">
        <div className="card bg-base-200 shadow-xl">
          <div className="card-body">
            {/* Header */}
            <div className="text-center mb-6">
              <div className="avatar placeholder mb-4">
                <div className="bg-linear-to-br from-primary to-secondary text-primary-content w-16 rounded-full">
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

            {/* Not Logged In Warning */}
            {!user && (
              <div className="alert alert-warning mb-4">
                <AlertCircle className="w-5 h-5" />
                <span>Please log in to upload flashcards</span>
              </div>
            )}

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
                  disabled={isLoading || !user}
                />
                <label className="label">
                  <span className="label-text-alt">
                    Expected format: {"{"}"deck_name": "...", "flashcards": [...]
                    {"}"}
                  </span>
                </label>
              </div>

              {file && !success && (
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
                  <span>Selected: {file.name}</span>
                </div>
              )}

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
                  disabled={!file || isLoading || !user}
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
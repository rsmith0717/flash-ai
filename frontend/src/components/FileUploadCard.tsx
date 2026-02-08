import { useNavigate } from '@tanstack/react-router'
import { Upload, AlertCircle, CheckCircle, LucideIcon } from 'lucide-react'
import { useState, ReactNode } from 'react'
import { useAuth } from '@/context/AuthContext'

interface FileUploadCardProps {
  // Appearance
  title: string
  description: string
  icon: LucideIcon
  iconGradient: string
  acceptedFileType: string
  fileExtension: string
  
  // Form fields
  showDeckNameField?: boolean
  additionalFields?: ReactNode
  
  // Behavior
  onSubmit: (file: File, deckName?: string) => Promise<void>
  buttonText?: string
  processingText?: string
  successMessage?: string
  
  // Styling
  buttonClass?: string
}

export default function FileUploadCard({
  title,
  description,
  icon: Icon,
  iconGradient,
  acceptedFileType,
  fileExtension,
  showDeckNameField = false,
  additionalFields,
  onSubmit,
  buttonText = 'Upload',
  processingText = 'Processing...',
  successMessage = 'Upload successful! Redirecting...',
  buttonClass = 'btn-primary',
}: FileUploadCardProps) {
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
      if (!selectedFile.name.endsWith(fileExtension)) {
        setError(`Please select a ${fileExtension} file`)
        setFile(null)
        return
      }
      setFile(selectedFile)
      setError(null)
      setSuccess(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!user) {
      setError('Please log in to upload files')
      return
    }

    if (!file) {
      setError('Please select a file')
      return
    }

    if (showDeckNameField && !deckName.trim()) {
      setError('Please enter a deck name')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      await onSubmit(file, showDeckNameField ? deckName : undefined)
      setSuccess(true)
      setTimeout(() => navigate({ to: '/' }), 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setIsLoading(false)
    }
  }

  const isSubmitDisabled = !file || isLoading || !user || (showDeckNameField && !deckName.trim())

  return (
    <div className="min-h-screen bg-base-100 py-16 px-4">
      <div className="container mx-auto max-w-2xl">
        <div className="card bg-base-200 shadow-xl border border-base-300">
          <div className="card-body">
            {/* Header */}
            <div className="text-center mb-6">
              <div className="avatar placeholder mb-4">
                <div className={`${iconGradient} text-primary-content w-16 rounded-full`}>
                  <Icon className="w-8 h-8" />
                </div>
              </div>
              <h1 className="card-title text-3xl justify-center mb-2">
                {title}
              </h1>
              <p className="text-base-content/70">
                {description}
              </p>
            </div>

            {/* Not Logged In Warning */}
            {!user && (
              <div className="alert alert-warning mb-4">
                <AlertCircle className="w-5 h-5" />
                <span>Please log in to upload files</span>
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
                <span>{successMessage}</span>
              </div>
            )}

            {/* Upload Form */}
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Deck Name Field (optional) */}
              {showDeckNameField && (
                <div className="form-control">
                  <label className="label">
                    <span className="label-text">Deck Name</span>
                  </label>
                  <input
                    type="text"
                    value={deckName}
                    onChange={(e) => setDeckName(e.target.value)}
                    placeholder="e.g., Biology Chapter 3"
                    className={`input input-bordered ${buttonClass.replace('btn-', 'input-')} w-full`}
                    disabled={isLoading || !user}
                    required={showDeckNameField}
                  />
                </div>
              )}

              {/* Additional Custom Fields */}
              {additionalFields}

              {/* File Input */}
              <div className="form-control">
                <label className="label">
                  <span className="label-text">{acceptedFileType} File</span>
                </label>
                <input
                  type="file"
                  accept={fileExtension}
                  onChange={handleFileChange}
                  className={`file-input file-input-bordered ${buttonClass.replace('btn-', 'file-input-')} w-full`}
                  disabled={isLoading || !user}
                />
                <label className="label">
                  <span className="label-text-alt">
                    Expected format: {fileExtension}
                  </span>
                </label>
              </div>

              {/* Selected File Info */}
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

              {/* Action Buttons */}
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
                  className={`btn ${buttonClass}`}
                  disabled={isSubmitDisabled}
                >
                  {isLoading ? (
                    <>
                      <span className="loading loading-spinner"></span>
                      {processingText}
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4" />
                      {buttonText}
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
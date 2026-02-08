import { createFileRoute } from '@tanstack/react-router'
import { FileText } from 'lucide-react'
import FileUploadCard from '@/components/FileUploadCard'

export const Route = createFileRoute('/upload-text')({
  component: TextUploadPage,
})

async function uploadTextFile(file: File, deckName: string): Promise<void> {
  const token = localStorage.getItem('access_token')
  
  if (!token) {
    throw new Error('No authentication token found. Please log in.')
  }

  const formData = new FormData()
  formData.append('file', file)
  formData.append('deck_name', deckName)

  const response = await fetch('http://localhost:8000/cards/deck/upload/text', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
    credentials: 'include',
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }))
    throw new Error(errorData.detail || 'Failed to upload and process document')
  }
}

function TextUploadPage() {
  const handleUpload = async (file: File, deckName?: string) => {
    if (!deckName) {
      throw new Error('Deck name is required')
    }
    return uploadTextFile(file, deckName)
  }

  return (
    <FileUploadCard
      title="Upload Text Document"
      description="AI will process your document and create flashcards"
      icon={FileText}
      iconGradient="bg-gradient-to-br from-secondary to-primary"
      acceptedFileType="Text"
      fileExtension=".txt"
      showDeckNameField={true}
      onSubmit={handleUpload}
      buttonText="Process Document"
      processingText="Processing..."
      successMessage="Document processed successfully! Redirecting..."
      buttonClass="btn-secondary"
      additionalFields={
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
          <span>
            Our AI will analyze your document and automatically generate
            question-answer pairs for effective studying.
          </span>
        </div>
      }
    />
  )
}
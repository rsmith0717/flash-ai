import { createFileRoute } from '@tanstack/react-router'
import { FileJson } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import FileUploadCard from '@/components/FileUploadCard'

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
  const uploadMutation = useMutation({
    mutationFn: uploadDeckFile,
  })

  const handleUpload = async (file: File) => {
    return uploadMutation.mutateAsync(file)
  }

  return (
    <FileUploadCard
      title="Upload JSON Deck"
      description="Upload a JSON file with flashcard questions and answers"
      icon={FileJson}
      iconGradient="bg-gradient-to-br from-primary to-secondary"
      acceptedFileType="JSON"
      fileExtension=".json"
      onSubmit={handleUpload}
      buttonText="Upload Deck"
      processingText="Uploading..."
      successMessage="Deck uploaded successfully! Redirecting..."
      buttonClass="btn-primary"
      additionalFields={
        <>
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
        </>
      }
    />
  )
}
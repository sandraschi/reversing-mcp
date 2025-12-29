'use client'

import { useState, useCallback } from 'react'

// Force dynamic rendering
export const dynamic = 'force-dynamic'
import { useRouter } from 'next/navigation'
import { useDropzone } from 'react-dropzone'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { useFileUpload, useAnalysisState } from '@/lib/mcp/hooks'
import { isValidBinaryFile, getFileTypeDescription, formatFileSize } from '@/lib/utils'
import {
  Upload,
  File,
  AlertCircle,
  CheckCircle,
  XCircle,
  Loader2,
  Search
} from 'lucide-react'

export default function LoaderPage() {
  const router = useRouter()
  const { upload, isUploading, progress, error: uploadError, uploadedFile } = useFileUpload()
  const { setFile, setResults } = useAnalysisState()
  const [analysisStarted, setAnalysisStarted] = useState(false)

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    if (!isValidBinaryFile(file)) {
      alert('Please select a valid binary file (.exe, .dll, .so, .bin, etc.)')
      return
    }

    try {
      await upload(file)
      setFile(file)
    } catch (err) {
      console.error('Upload failed:', err)
    }
  }, [upload, setFile])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/octet-stream': ['.exe', '.dll', '.so', '.dylib', '.bin', '.com', '.sys', '.drv']
    },
    multiple: false,
    disabled: isUploading
  })

  const startAnalysis = async () => {
    if (!uploadedFile) return

    setAnalysisStarted(true)

    try {
      // Get selected tools from checkboxes
      const selectedTools: string[] = []
      const checkboxes = document.querySelectorAll('input[type="checkbox"]:checked')
      checkboxes.forEach((checkbox) => {
        const id = (checkbox as HTMLInputElement).id
        if (id === 'basic-analysis') {
          selectedTools.push('file', 'strings', 'entropy')
        } else if (id === 'pe-analysis') {
          selectedTools.push('pefile')
        } else if (id === 'ghidra-analysis') {
          selectedTools.push('ghidra')
        }
      })

      // Use the new analyzeUploadedFile function
      const { analyzeUploadedFile } = await import('@/lib/mcp/client')
      const analysisResult = await analyzeUploadedFile(uploadedFile, selectedTools.length > 0 ? selectedTools : undefined)

      setResults(analysisResult)
      router.push('/analysis')
    } catch (err) {
      console.error('Analysis failed:', err)
      setAnalysisStarted(false)
      alert(`Analysis failed: ${err instanceof Error ? err.message : 'Unknown error'}`)
    }
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold mb-2">Load Binary for Analysis</h1>
        <p className="text-muted-foreground">
          Upload an executable file to begin reverse engineering analysis
        </p>
      </div>

      {/* Upload Area */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="w-5 h-5" />
            File Upload
          </CardTitle>
          <CardDescription>
            Drag and drop a binary file or click to browse. Supports EXE, DLL, SO, BIN and other executable formats.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              isDragActive
                ? 'border-primary bg-primary/5'
                : 'border-muted-foreground/25 hover:border-muted-foreground/50'
            } ${isUploading ? 'opacity-50 pointer-events-none' : ''}`}
          >
            <input {...getInputProps()} />
            <div className="flex flex-col items-center gap-4">
              {isUploading ? (
                <Loader2 className="w-12 h-12 text-muted-foreground animate-spin" />
              ) : (
                <Upload className="w-12 h-12 text-muted-foreground" />
              )}

              {isDragActive ? (
                <p className="text-lg font-medium">Drop the file here...</p>
              ) : (
                <div>
                  <p className="text-lg font-medium mb-2">
                    {isUploading ? 'Uploading...' : 'Choose a binary file'}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    or drag and drop it here
                  </p>
                </div>
              )}

              {/* Supported formats */}
              <div className="flex flex-wrap gap-2 justify-center mt-4">
                {['.exe', '.dll', '.so', '.bin', '.com', '.sys'].map(ext => (
                  <Badge key={ext} variant="outline">{ext}</Badge>
                ))}
              </div>
            </div>
          </div>

          {/* Upload Progress */}
          {isUploading && (
            <div className="mt-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span>Uploading...</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <Progress value={progress} className="w-full" />
            </div>
          )}

          {/* Upload Error */}
          {uploadError && (
            <div className="mt-4 p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
              <div className="flex items-center gap-2 text-destructive">
                <XCircle className="w-4 h-4" />
                <span className="text-sm">{uploadError}</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* File Info */}
      {uploadedFile && (
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <File className="w-5 h-5" />
              File Information
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-muted-foreground">File Name</label>
                <p className="text-sm font-mono">{uploadedFile.name}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Size</label>
                <p className="text-sm">{formatFileSize(uploadedFile.size)}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Type</label>
                <p className="text-sm">{getFileTypeDescription(uploadedFile)}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Last Modified</label>
                <p className="text-sm">{new Date(uploadedFile.lastModified).toLocaleString()}</p>
              </div>
            </div>

            {/* Validation Status */}
            <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center gap-2 text-green-700">
                <CheckCircle className="w-4 h-4" />
                <span className="text-sm">File validated successfully - ready for analysis</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Analysis Options */}
      {uploadedFile && !isUploading && (
        <Card>
          <CardHeader>
            <CardTitle>Analysis Configuration</CardTitle>
            <CardDescription>
              Choose analysis options and start the reverse engineering process
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Analysis Options */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="basic-analysis"
                    defaultChecked
                    className="rounded"
                  />
                  <label htmlFor="basic-analysis" className="text-sm">
                    Basic Analysis (file type, strings, entropy)
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="pe-analysis"
                    defaultChecked
                    className="rounded"
                  />
                  <label htmlFor="pe-analysis" className="text-sm">
                    PE Analysis (Windows executables)
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="ghidra-analysis"
                    defaultChecked
                    className="rounded"
                  />
                  <label htmlFor="ghidra-analysis" className="text-sm">
                    Ghidra Analysis (decompilation)
                  </label>
                </div>
              </div>

              {/* Start Analysis Button */}
              <div className="flex gap-4 pt-4">
                <Button
                  onClick={startAnalysis}
                  disabled={analysisStarted}
                  className="flex-1"
                >
                  {analysisStarted ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Starting Analysis...
                    </>
                  ) : (
                    <>
                      <Search className="w-4 h-4 mr-2" />
                      Start Analysis
                    </>
                  )}
                </Button>

                <Button
                  variant="outline"
                  onClick={() => {
                    // Clear uploaded file
                    window.location.reload()
                  }}
                >
                  Clear & Upload Another
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Help Text */}
      <div className="mt-8 text-center text-muted-foreground">
        <p className="text-sm">
          Need help? Check the{' '}
          <a href="/help" className="text-primary hover:underline">
            documentation
          </a>{' '}
          or visit{' '}
          <a
            href="https://github.com/sandraschi/reversing-mcp"
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:underline"
          >
            GitHub
          </a>
        </p>
      </div>
    </div>
  )
}
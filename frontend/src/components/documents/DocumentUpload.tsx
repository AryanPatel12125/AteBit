"use client";

import React, { useState, useRef } from 'react';
import { Upload, FileText, AlertCircle, CheckCircle, Loader2, X } from 'lucide-react';
import { useDocumentUpload } from '@/lib/api/hooks';
import { DocumentUploadResponse } from '@/lib/api/client';

interface DocumentUploadProps {
  onUploadSuccess?: (result: DocumentUploadResponse) => void;
  onUploadError?: (error: string) => void;
}

export function DocumentUpload({ onUploadSuccess, onUploadError }: DocumentUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const uploadMutation = useDocumentUpload();

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      setSelectedFile(files[0]);
      if (!title) {
        setTitle(files[0].name);
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files[0]) {
      setSelectedFile(files[0]);
      if (!title) {
        setTitle(files[0].name);
      }
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      const result = await uploadMutation.mutateAsync({
        file: selectedFile,
        title: title || selectedFile.name,
      });

      onUploadSuccess?.(result);
      
      // Reset form
      setSelectedFile(null);
      setTitle('');
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      onUploadError?.(errorMessage);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getSupportedFormats = () => {
    return ['.pdf', '.doc', '.docx', '.txt'];
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Upload Area */}
      <div
        className={`
          border-2 border-dashed rounded-lg p-8 text-center transition-colors
          ${dragActive 
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
            : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
          }
          ${uploadMutation.isPending ? 'pointer-events-none opacity-50' : ''}
        `}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf,.doc,.docx,.txt"
          onChange={handleFileSelect}
          disabled={uploadMutation.isPending}
        />

        <div className="space-y-4">
          <div className="flex justify-center">
            {uploadMutation.isPending ? (
              <Loader2 className="w-12 h-12 text-blue-500 animate-spin" />
            ) : (
              <Upload className="w-12 h-12 text-gray-400" />
            )}
          </div>

          <div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              {uploadMutation.isPending ? 'Processing Document...' : 'Upload Legal Document'}
            </h3>
            <p className="text-gray-600 dark:text-gray-300">
              {uploadMutation.isPending 
                ? 'Analyzing document with AI...' 
                : 'Drag and drop your document here, or click to browse'
              }
            </p>
          </div>

          <div className="text-sm text-gray-500">
            Supported formats: {getSupportedFormats().join(', ')} • Max size: 10MB
          </div>
        </div>
      </div>

      {/* Selected File Info */}
      {selectedFile && (
        <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <FileText className="w-8 h-8 text-blue-500" />
              <div>
                <p className="font-medium text-gray-900 dark:text-white">
                  {selectedFile.name}
                </p>
                <p className="text-sm text-gray-500">
                  {formatFileSize(selectedFile.size)} • {selectedFile.type || 'Unknown type'}
                </p>
              </div>
            </div>
            <button
              onClick={() => {
                setSelectedFile(null);
                setTitle('');
                if (fileInputRef.current) {
                  fileInputRef.current.value = '';
                }
              }}
              className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              disabled={uploadMutation.isPending}
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Title Input */}
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Document Title (Optional)
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter a title for this document"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-900 dark:text-white bg-white dark:bg-gray-700 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={uploadMutation.isPending}
            />
          </div>

          {/* Upload Button */}
          <div className="mt-4">
            <button
              onClick={handleUpload}
              disabled={!selectedFile || uploadMutation.isPending}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-md font-medium transition-colors flex items-center justify-center gap-2"
            >
              {uploadMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  Upload & Analyze
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Error Display */}
      {uploadMutation.error && (
        <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
            <p className="text-red-700 dark:text-red-300 font-medium">Upload Failed</p>
          </div>
          <p className="text-red-600 dark:text-red-400 text-sm mt-1">
            {uploadMutation.error.message}
          </p>
        </div>
      )}
    </div>
  );
}
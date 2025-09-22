"use client";

import React from 'react';
import { CheckCircle, AlertTriangle, XCircle, Clock, FileText, Shield } from 'lucide-react';
import { DocumentUploadResponse, DocumentAnalysisResult } from '@/lib/api/client';
import { useDocumentAnalysis } from '@/lib/api/hooks';

interface DocumentAnalysisProps {
  uploadResult?: DocumentUploadResponse;
  documentId?: string;
  className?: string;
}

export function DocumentAnalysis({ uploadResult, documentId, className = '' }: DocumentAnalysisProps) {
  // Use the hook to fetch analysis if we have a document ID but no upload result
  const { data: analysisData, isLoading, error } = useDocumentAnalysis(
    documentId || '',
    !!documentId && !uploadResult
  );

  // Use either the upload result or the fetched analysis data
  const analysis = uploadResult?.analysis || analysisData?.result;
  const status = uploadResult?.analysis?.status || analysisData?.status || 'pending';
  const title = uploadResult?.title || 'Document Analysis';

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'critical': return 'text-red-600 bg-red-100 dark:bg-red-900/20 dark:text-red-400';
      case 'high': return 'text-orange-600 bg-orange-100 dark:bg-orange-900/20 dark:text-orange-400';
      case 'medium': return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/20 dark:text-yellow-400';
      case 'low': return 'text-green-600 bg-green-100 dark:bg-green-900/20 dark:text-green-400';
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-800 dark:text-gray-400';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-6 h-6 text-green-500" />;
      case 'pending':
        return <Clock className="w-6 h-6 text-yellow-500 animate-pulse" />;
      case 'failed':
        return <XCircle className="w-6 h-6 text-red-500" />;
      default:
        return <FileText className="w-6 h-6 text-gray-500" />;
    }
  };

  if (isLoading) {
    return (
      <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 ${className}`}>
        <div className="flex items-center gap-3 mb-4">
          <Clock className="w-6 h-6 text-yellow-500 animate-pulse" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Analyzing Document...
          </h3>
        </div>
        <div className="space-y-3">
          <div className="animate-pulse bg-gray-200 dark:bg-gray-700 h-4 rounded w-3/4"></div>
          <div className="animate-pulse bg-gray-200 dark:bg-gray-700 h-4 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 ${className}`}>
        <div className="flex items-center gap-3 mb-4">
          <XCircle className="w-6 h-6 text-red-500" />
          <h3 className="text-lg font-semibold text-red-700 dark:text-red-400">
            Analysis Failed
          </h3>
        </div>
        <p className="text-red-600 dark:text-red-400">
          {error.message}
        </p>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 ${className}`}>
        <div className="text-center py-8">
          <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No Analysis Available
          </h3>
          <p className="text-gray-600 dark:text-gray-300">
            Upload a document to see AI-powered analysis results.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-md ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          {getStatusIcon()}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {title}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-300 capitalize">
              Status: {status}
            </p>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Summary */}
        {analysis.summary && (
          <div>
            <h4 className="text-md font-medium text-gray-900 dark:text-white mb-3 flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Summary
            </h4>
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                {analysis.summary}
              </p>
            </div>
          </div>
        )}

        {/* Risks */}
        {analysis.risks && analysis.risks.length > 0 && (
          <div>
            <h4 className="text-md font-medium text-gray-900 dark:text-white mb-3 flex items-center gap-2">
              <Shield className="w-5 h-5" />
              Risk Assessment
            </h4>
            <div className="space-y-3">
              {analysis.risks.map((risk, index) => (
                <div
                  key={index}
                  className={`p-4 rounded-lg border ${getRiskColor(risk.level)}`}
                >
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 mt-0.5 flex-shrink-0" />
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium capitalize">{risk.level} Risk</span>
                        <span className="text-xs px-2 py-1 rounded bg-white/50 dark:bg-black/20">
                          {risk.category}
                        </span>
                      </div>
                      <p className="text-sm leading-relaxed">{risk.description}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Key Terms */}
        {analysis.key_terms && analysis.key_terms.length > 0 && (
          <div>
            <h4 className="text-md font-medium text-gray-900 dark:text-white mb-3">
              Key Terms
            </h4>
            <div className="grid gap-3">
              {analysis.key_terms.map((term, index) => (
                <div
                  key={index}
                  className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4"
                >
                  <div className="flex items-start justify-between mb-2">
                    <h5 className="font-medium text-gray-900 dark:text-white">
                      {term.term}
                    </h5>
                    <span
                      className={`text-xs px-2 py-1 rounded capitalize ${
                        term.importance === 'high'
                          ? 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400'
                          : term.importance === 'medium'
                          ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/20 dark:text-yellow-400'
                          : 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400'
                      }`}
                    >
                      {term.importance}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
                    {term.definition}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {analysis.recommendations && analysis.recommendations.length > 0 && (
          <div>
            <h4 className="text-md font-medium text-gray-900 dark:text-white mb-3">
              Recommendations
            </h4>
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
              <ul className="space-y-2">
                {analysis.recommendations.map((rec, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                    <span className="text-blue-700 dark:text-blue-300 text-sm leading-relaxed">
                      {rec}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
"use client";

import React, { useState } from 'react';
import { FileText, Upload, Clock, CheckCircle, AlertTriangle, Globe, Eye, BarChart3, Shield, BookOpen, Zap, FileCheck } from 'lucide-react';

interface FakeAnalysisResult {
  summary: {
    text: string;
    confidence: number;
  };
  keyPoints: Array<{
    point: string;
    importance: 'high' | 'medium' | 'low';
    section: string;
  }>;
  risks: Array<{
    level: 'high' | 'medium' | 'low';
    description: string;
    category: string;
    severity: number;
  }>;
  translation: {
    detectedLanguage: string;
    confidence: number;
    availableTranslations: string[];
    sampleTranslations: { [key: string]: string };
  };
  metadata: {
    wordCount: number;
    readingTime: string;
    complexity: string;
    documentType: string;
  };
}

type ProcessingStage = 'idle' | 'uploading' | 'extracting' | 'analyzing' | 'translating' | 'complete';

export default function DocumentDemoPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [processingStage, setProcessingStage] = useState<ProcessingStage>('idle');
  const [analysisResult, setAnalysisResult] = useState<FakeAnalysisResult | null>(null);
  const [progress, setProgress] = useState(0);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setAnalysisResult(null);
      setProcessingStage('idle');
      setProgress(0);
    }
  };

  const generateFakeAnalysis = (file: File): FakeAnalysisResult => {
    const wordCount = Math.floor(Math.random() * 2000) + 500;
    const docTypes = ['Legal Contract', 'Business Report', 'Financial Document', 'Technical Specification', 'Policy Document'];
    const documentType = docTypes[Math.floor(Math.random() * docTypes.length)];
    
    return {
      summary: {
        text: `This ${documentType.toLowerCase()} contains ${wordCount} words and presents comprehensive information requiring stakeholder attention. The document demonstrates professional structure with clear sections and actionable content. Analysis indicates standard compliance formatting with medium complexity business terminology suitable for executive review and strategic decision-making.`,
        confidence: 0.94
      },
      keyPoints: [
        { point: `Document type: ${documentType}`, importance: 'high', section: 'classification' },
        { point: `Content volume: ${wordCount} words, ~${Math.ceil(wordCount / 200)} min read`, importance: 'medium', section: 'metadata' },
        { point: 'Professional formatting with structured sections detected', importance: 'high', section: 'structure' },
        { point: 'Contains actionable business information and recommendations', importance: 'high', section: 'content' },
        { point: 'Compliance-ready documentation with standard legal terminology', importance: 'medium', section: 'legal' },
        { point: 'Suitable for multi-stakeholder review and approval process', importance: 'medium', section: 'workflow' }
      ],
      risks: [
        { level: 'low', description: 'Standard business content with minimal risk exposure', category: 'Content Risk', severity: 2 },
        { level: 'medium', description: 'Manual legal review recommended for compliance verification', category: 'Compliance', severity: 4 },
        { level: 'low', description: 'No personally identifiable information detected in initial scan', category: 'Privacy', severity: 1 },
        { level: 'medium', description: 'Financial data present - consider access restrictions', category: 'Financial', severity: 3 }
      ],
      translation: {
        detectedLanguage: 'English (US)',
        confidence: 0.97,
        availableTranslations: ['Spanish', 'French', 'German', 'Chinese (Simplified)', 'Japanese', 'Portuguese'],
        sampleTranslations: {
          'Spanish': 'Este documento legal contiene información integral que requiere atención de las partes interesadas...',
          'French': 'Ce document juridique contient des informations complètes nécessitant l\'attention des parties prenantes...',
          'German': 'Dieses Rechtsdokument enthält umfassende Informationen, die die Aufmerksamkeit der Stakeholder erfordern...'
        }
      },
      metadata: {
        wordCount,
        readingTime: `${Math.ceil(wordCount / 200)} minutes`,
        complexity: ['Low', 'Medium', 'High'][Math.floor(Math.random() * 3)],
        documentType
      }
    };
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    const stages: ProcessingStage[] = ['uploading', 'extracting', 'analyzing', 'translating', 'complete'];
    let currentStageIndex = 0;

    // Simulate upload process
    setProcessingStage(stages[currentStageIndex]);
    setProgress(0);

    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          currentStageIndex++;
          if (currentStageIndex < stages.length) {
            setProcessingStage(stages[currentStageIndex]);
            return 0;
          } else {
            clearInterval(progressInterval);
            // Generate and show fake analysis
            setTimeout(() => {
              setAnalysisResult(generateFakeAnalysis(selectedFile));
            }, 500);
            return 100;
          }
        }
        return prev + Math.random() * 15 + 5;
      });
    }, 200);
  };

  const reset = () => {
    setSelectedFile(null);
    setProcessingStage('idle');
    setAnalysisResult(null);
    setProgress(0);
  };

  const getStageInfo = (stage: ProcessingStage) => {
    const stages = {
      idle: { icon: Upload, text: 'Ready to upload', color: 'text-gray-500' },
      uploading: { icon: Upload, text: 'Uploading document...', color: 'text-blue-500' },
      extracting: { icon: FileCheck, text: 'Extracting text content...', color: 'text-yellow-500' },
      analyzing: { icon: BarChart3, text: 'AI analysis in progress...', color: 'text-purple-500' },
      translating: { icon: Globe, text: 'Processing translations...', color: 'text-green-500' },
      complete: { icon: CheckCircle, text: 'Analysis complete!', color: 'text-green-600' }
    };
    return stages[stage];
  };

  const stageInfo = getStageInfo(processingStage);
  const StageIcon = stageInfo.icon;

  if (analysisResult) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
        <div className="max-w-6xl mx-auto px-4 py-8">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Document Analysis Complete</h1>
            <p className="text-gray-600 dark:text-gray-300">Comprehensive AI-powered analysis results</p>
            <button 
              onClick={reset}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Analyze Another Document
            </button>
          </div>

          {/* Analysis Results */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Summary */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
              <div className="flex items-center gap-2 mb-4">
                <BookOpen className="w-6 h-6 text-blue-600" />
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Summary</h2>
                <span className="ml-auto text-sm bg-green-100 text-green-800 px-2 py-1 rounded-full">
                  {(analysisResult.summary.confidence * 100).toFixed(0)}% confidence
                </span>
              </div>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed">{analysisResult.summary.text}</p>
            </div>

            {/* Document Metadata */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
              <div className="flex items-center gap-2 mb-4">
                <FileText className="w-6 h-6 text-green-600" />
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Document Info</h2>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Type:</span>
                  <span className="font-medium text-gray-900 dark:text-white">{analysisResult.metadata.documentType}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Word Count:</span>
                  <span className="font-medium text-gray-900 dark:text-white">{analysisResult.metadata.wordCount.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Reading Time:</span>
                  <span className="font-medium text-gray-900 dark:text-white">{analysisResult.metadata.readingTime}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Complexity:</span>
                  <span className="font-medium text-gray-900 dark:text-white">{analysisResult.metadata.complexity}</span>
                </div>
              </div>
            </div>

            {/* Key Points */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
              <div className="flex items-center gap-2 mb-4">
                <Eye className="w-6 h-6 text-purple-600" />
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Key Points</h2>
              </div>
              <div className="space-y-3">
                {analysisResult.keyPoints.map((point, index) => (
                  <div key={index} className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div className={`w-2 h-2 rounded-full mt-2 ${
                      point.importance === 'high' ? 'bg-red-500' : 
                      point.importance === 'medium' ? 'bg-yellow-500' : 'bg-green-500'
                    }`}></div>
                    <div className="flex-1">
                      <p className="text-gray-900 dark:text-white">{point.point}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400 capitalize">{point.section}</p>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      point.importance === 'high' ? 'bg-red-100 text-red-800' : 
                      point.importance === 'medium' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'
                    }`}>
                      {point.importance}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Risk Analysis */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
              <div className="flex items-center gap-2 mb-4">
                <Shield className="w-6 h-6 text-red-600" />
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Risk Analysis</h2>
              </div>
              <div className="space-y-3">
                {analysisResult.risks.map((risk, index) => (
                  <div key={index} className="p-3 border rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-gray-900 dark:text-white">{risk.category}</span>
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        risk.level === 'high' ? 'bg-red-100 text-red-800' : 
                        risk.level === 'medium' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'
                      }`}>
                        {risk.level}
                      </span>
                    </div>
                    <p className="text-gray-600 dark:text-gray-400 text-sm">{risk.description}</p>
                    <div className="mt-2">
                      <div className={`w-full bg-gray-200 rounded-full h-1.5 ${
                        risk.level === 'high' ? 'bg-red-200' : 
                        risk.level === 'medium' ? 'bg-yellow-200' : 'bg-green-200'
                      }`}>
                        <div 
                          className={`h-1.5 rounded-full ${
                            risk.level === 'high' ? 'bg-red-600' : 
                            risk.level === 'medium' ? 'bg-yellow-600' : 'bg-green-600'
                          }`}
                          style={{ width: `${(risk.severity / 10) * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Translation */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 lg:col-span-2">
              <div className="flex items-center gap-2 mb-4">
                <Globe className="w-6 h-6 text-indigo-600" />
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Translation Analysis</h2>
                <span className="ml-auto text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                  {(analysisResult.translation.confidence * 100).toFixed(0)}% confidence
                </span>
              </div>
              <div className="mb-4">
                <p className="text-gray-700 dark:text-gray-300 mb-2">
                  <strong>Detected Language:</strong> {analysisResult.translation.detectedLanguage}
                </p>
                <p className="text-gray-700 dark:text-gray-300 mb-4">
                  <strong>Available Translations:</strong> {analysisResult.translation.availableTranslations.join(', ')}
                </p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {Object.entries(analysisResult.translation.sampleTranslations).map(([language, text]) => (
                  <div key={language} className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <h4 className="font-medium text-gray-900 dark:text-white mb-2 capitalize">{language}</h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400 italic">"{text}"</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Demo Notice */}
          <div className="mt-8 bg-gradient-to-r from-purple-100 to-pink-100 dark:from-purple-900 dark:to-pink-900 rounded-xl p-6 text-center">
            <Zap className="w-8 h-8 text-purple-600 mx-auto mb-2" />
            <p className="text-purple-800 dark:text-purple-200 font-medium">
              🎭 Demo Mode - This is a comprehensive AI analysis simulation for presentation purposes
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="max-w-4xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            AI Document Analyzer
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300">
            Upload any document for comprehensive AI-powered analysis
          </p>
        </div>

        {/* Upload Section */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 mb-8">
          {processingStage === 'idle' ? (
            <>
              {/* File Upload */}
              <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl p-12 text-center">
                <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  Select Document to Analyze
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  PDF, DOCX, TXT files supported • Maximum 10MB
                </p>
                <input
                  type="file"
                  accept=".pdf,.docx,.txt,.doc"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="file-upload"
                />
                <label
                  htmlFor="file-upload"
                  className="inline-flex items-center px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 cursor-pointer transition-colors"
                >
                  <Upload className="w-5 h-5 mr-2" />
                  Choose File
                </label>
              </div>

              {/* Selected File */}
              {selectedFile && (
                <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-700">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <FileText className="w-8 h-8 text-blue-600" />
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">{selectedFile.name}</p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {(selectedFile.size / 1024 / 1024).toFixed(1)} MB
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={handleUpload}
                      className="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
                    >
                      <Zap className="w-4 h-4" />
                      Start Analysis
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : (
            /* Processing Status */
            <div className="text-center py-12">
              <div className="flex justify-center mb-6">
                <div className={`p-4 rounded-full bg-blue-100 dark:bg-blue-900 ${
                  processingStage !== 'complete' ? 'animate-pulse' : ''
                }`}>
                  <StageIcon className={`w-12 h-12 ${stageInfo.color}`} />
                </div>
              </div>
              
              <h3 className="text-2xl font-semibold text-gray-900 dark:text-white mb-2">
                {stageInfo.text}
              </h3>
              
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Processing: {selectedFile?.name}
              </p>

              {/* Progress Bar */}
              <div className="max-w-md mx-auto mb-6">
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                  <div 
                    className="bg-gradient-to-r from-blue-500 to-purple-600 h-3 rounded-full transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
                <p className="text-sm text-gray-500 mt-2">{Math.round(progress)}% complete</p>
              </div>

              {/* Processing Steps */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl mx-auto">
                {[
                  { stage: 'uploading', icon: Upload, label: 'Upload' },
                  { stage: 'extracting', icon: FileCheck, label: 'Extract' },
                  { stage: 'analyzing', icon: BarChart3, label: 'Analyze' },
                  { stage: 'translating', icon: Globe, label: 'Translate' }
                ].map((step) => {
                  const StepIcon = step.icon;
                  const isActive = processingStage === step.stage;
                  const isComplete = ['uploading', 'extracting', 'analyzing', 'translating'].indexOf(processingStage) > 
                                   ['uploading', 'extracting', 'analyzing', 'translating'].indexOf(step.stage);
                  
                  return (
                    <div key={step.stage} className="text-center">
                      <div className={`p-3 rounded-full mx-auto mb-2 w-12 h-12 flex items-center justify-center ${
                        isActive ? 'bg-blue-100 animate-pulse' : 
                        isComplete ? 'bg-green-100' : 'bg-gray-100'
                      }`}>
                        <StepIcon className={`w-5 h-5 ${
                          isActive ? 'text-blue-600' : 
                          isComplete ? 'text-green-600' : 'text-gray-400'
                        }`} />
                      </div>
                      <p className={`text-sm font-medium ${
                        isActive ? 'text-blue-600' : 
                        isComplete ? 'text-green-600' : 'text-gray-400'
                      }`}>
                        {step.label}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Features Preview */}
        {processingStage === 'idle' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { icon: BookOpen, title: 'Smart Summary', desc: 'AI-powered document summarization' },
              { icon: Eye, title: 'Key Points', desc: 'Extract important insights' },
              { icon: Shield, title: 'Risk Analysis', desc: 'Identify potential risks' },
              { icon: Globe, title: 'Translation', desc: 'Multi-language support' }
            ].map((feature, index) => {
              const FeatureIcon = feature.icon;
              return (
                <div key={index} className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-lg text-center">
                  <FeatureIcon className="w-12 h-12 text-blue-600 mx-auto mb-4" />
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-2">{feature.title}</h3>
                  <p className="text-gray-600 dark:text-gray-400 text-sm">{feature.desc}</p>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
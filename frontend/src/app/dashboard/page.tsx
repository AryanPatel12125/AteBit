"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Upload,
  FileText,
  AlertTriangle,
  Languages,
  ArrowLeft,
  Plus,
} from "lucide-react";

export default function Dashboard() {
  const router = useRouter();
  const [documents] = useState([
    {
      id: 1,
      name: "Employment_Contract_2024.pdf",
      uploadDate: "2024-01-15",
      status: "completed",
      type: "Employment Contract",
      analysisComplete: true,
    },
    {
      id: 2,
      name: "NDA_TechCorp.docx",
      uploadDate: "2024-01-14",
      status: "processing",
      type: "Non-Disclosure Agreement",
      analysisComplete: false,
    },
  ]);

  const stats = [
    { label: "Documents Processed", value: "156", change: "+12 this month" },
    { label: "Time Saved", value: "240 hrs", change: "+18 hrs this week" },
    { label: "Risk Issues Found", value: "23", change: "3 high priority" },
    { label: "Languages Used", value: "8", change: "2 new this month" },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push("/")}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Home
            </Button>
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Document Analysis Dashboard
              </h1>
              <p className="text-gray-600 dark:text-gray-300">
                Manage and analyze your legal documents with AI-powered insights
              </p>
            </div>
          </div>
          <Button size="lg" className="bg-blue-600 hover:bg-blue-700">
            <Plus className="h-5 w-5 mr-2" />
            Upload Document
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {stats.map((stat) => (
            <Card key={stat.label}>
              <CardContent className="p-6">
                <div className="text-2xl font-bold text-blue-600 mb-1">
                  {stat.value}
                </div>
                <div className="text-sm font-medium mb-1">{stat.label}</div>
                <div className="text-xs text-gray-500">{stat.change}</div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Upload Area */}
          <Card>
            <CardHeader>
              <CardTitle>Upload New Document</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="border-2 border-dashed border-blue-300 dark:border-blue-600 rounded-lg p-8 text-center hover:border-blue-400 dark:hover:border-blue-500 transition-colors cursor-pointer">
                <Upload className="h-12 w-12 text-blue-600 mx-auto mb-4" />
                <h3 className="font-semibold mb-2">Upload New Document</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  Drag & drop or click to select files
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-500">
                  Supports: PDF, DOCX, TXT (Max 10MB)
                </p>
                <Button className="mt-4">
                  <Upload className="h-4 w-4 mr-2" />
                  Choose File
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Recent Documents */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Documents</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    className="flex items-center justify-between p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
                  >
                    <div className="flex items-center space-x-3">
                      <FileText className="h-5 w-5 text-blue-600" />
                      <div>
                        <p className="font-medium text-sm">{doc.name}</p>
                        <p className="text-xs text-gray-500">{doc.type}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge
                        variant={
                          doc.status === "completed" ? "default" : "secondary"
                        }
                      >
                        {doc.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Analysis Section */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>AI Analysis Features</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="bg-blue-100 dark:bg-blue-900/30 p-4 rounded-full inline-block mb-4">
                  <FileText className="h-8 w-8 text-blue-600" />
                </div>
                <h3 className="font-semibold mb-2">Simplify</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Convert complex legalese into plain English
                </p>
              </div>
              
              <div className="text-center">
                <div className="bg-red-100 dark:bg-red-900/30 p-4 rounded-full inline-block mb-4">
                  <AlertTriangle className="h-8 w-8 text-red-600" />
                </div>
                <h3 className="font-semibold mb-2">Analyze Risks</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Identify potential risks and unfavorable terms
                </p>
              </div>
              
              <div className="text-center">
                <div className="bg-green-100 dark:bg-green-900/30 p-4 rounded-full inline-block mb-4">
                  <Languages className="h-8 w-8 text-green-600" />
                </div>
                <h3 className="font-semibold mb-2">Translate</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Get analysis in multiple languages
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
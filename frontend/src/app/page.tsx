"use client";

import React from "react";
import { useRouter } from "next/navigation";
import {
  FileText,
  Search,
  Globe,
  AlertTriangle,
  CheckCircle,
  Shield,
  Clock,
  Users,
  ArrowRight,
} from "lucide-react";
import { LandingHeader } from "@/components/layout/LandingHeader";

export default function Home() {
  const router = useRouter();

  const handleGetStarted = () => {
    router.push("/dashboard");
  };

  const services = [
    {
      icon: FileText,
      title: "Simplify",
      description:
        "Convert complex legalese into 12-year-old reading level language",
    },
    {
      icon: Search,
      title: "Analyze",
      description:
        "Automatically flag risks, hidden fees, and unfavorable terms",
    },
    {
      icon: Globe,
      title: "Translate",
      description:
        "Get document analysis in multiple languages for global accessibility",
    },
  ];

  const trustIndicators = [
    { icon: CheckCircle, label: "Zero Cost Analysis" },
    { icon: Shield, label: "Professional-Grade Insights" },
    { icon: Clock, label: "30-Second Results" },
    { icon: Users, label: "Trusted by 50,000+ Users" },
  ];

  const stats = [
    { number: "90%", label: "of people don't read terms of service" },
    { number: "$500+", label: "average cost per hour for legal consultation" },
    { number: "30 sec", label: "to get complete document analysis" },
  ];

  return (
    <div className="min-h-screen transition-colors duration-300">
      <div className="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-white">
        <LandingHeader />

        {/* Hero Section */}
        <section className="pt-20 pb-16 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-white to-indigo-50 dark:from-gray-900 dark:via-gray-900 dark:to-indigo-900/20"></div>
          <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>

          <div className="max-w-7xl mx-auto relative">
            <div className="text-center max-w-4xl mx-auto">
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 dark:text-white mb-6 leading-tight">
                Legal Documents Made
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400">
                  {" "}
                  Simple for Everyone
                </span>
              </h1>

              <p className="text-xl sm:text-2xl text-gray-600 dark:text-gray-300 mb-4 leading-relaxed">
                From contracts to terms of service – our AI turns complexity
                into clear, easy-to-read summaries you can trust.
              </p>

              <p className="text-lg text-gray-500 dark:text-gray-400 mb-8">
                — no law degree required —
              </p>

              <div className="bg-white dark:bg-gray-800 rounded-3xl p-6 mb-8 shadow-xl border border-gray-200 dark:border-gray-700 inline-block">
                <p className="text-lg text-gray-700 dark:text-gray-300 font-medium">
                  Get instant insights, identify risks, and understand what
                  you're signing in under
                  <span className="text-blue-600 dark:text-blue-400 font-bold">
                    {" "}
                    30 seconds
                  </span>
                </p>
              </div>

              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                <button
                  onClick={handleGetStarted}
                  className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-8 py-4 rounded-3xl text-lg font-semibold shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200 flex items-center gap-2 group"
                >
                  Get Started Free
                  <ArrowRight
                    size={20}
                    className="group-hover:translate-x-1 transition-transform"
                  />
                </button>
                <button
                  onClick={() => window.open("#how-it-works", "_self")}
                  className="border-2 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-blue-600 dark:hover:border-blue-400 hover:text-blue-600 dark:hover:text-blue-400 px-8 py-4 rounded-xl text-lg font-semibold transition-all duration-200"
                >
                  Watch Demo
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Trust Indicators */}
        <section className="py-8 px-4 sm:px-6 lg:px-8 bg-gray-50 dark:bg-gray-800/50">
          <div className="max-w-7xl mx-auto">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              {trustIndicators.map((indicator, index) => (
                <div
                  key={index}
                  className="flex flex-col items-center text-center"
                >
                  <div className="bg-blue-100 dark:bg-blue-900/30 p-3 rounded-full mb-2">
                    <indicator.icon
                      size={24}
                      className="text-blue-600 dark:text-blue-400"
                    />
                  </div>
                  <span className="text-sm font-medium text-gray-600 dark:text-gray-300">
                    {indicator.label}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Services Section */}
        <section id="features" className="py-20 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 dark:text-white mb-4">
                Democratizing Legal Document Understanding
              </h2>
              <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
                Making complex legal language accessible to everyone through
                cutting-edge AI technology
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              {services.map((service, index) => (
                <div
                  key={index}
                  className="bg-white dark:bg-gray-800 p-8 rounded-3xl shadow-lg hover:shadow-xl transition-all duration-300 border border-gray-200 dark:border-gray-700 group hover:-translate-y-1"
                >
                  <div className="bg-gradient-to-br from-blue-100 to-indigo-100 dark:from-blue-900/30 dark:to-indigo-900/30 p-4 rounded-2xl inline-block mb-6 group-hover:scale-110 transition-transform duration-300">
                    <service.icon
                      size={32}
                      className="text-blue-600 dark:text-blue-400"
                    />
                  </div>
                  <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                    {service.title}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-300 text-lg leading-relaxed">
                    {service.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Problem/Solution Section */}
        <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-gray-50 to-blue-50 dark:from-gray-800 dark:to-blue-900/10">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16">
              <div className="bg-red-100 dark:bg-red-900/30 p-4 rounded-full inline-block mb-6">
                <AlertTriangle
                  size={48}
                  className="text-red-600 dark:text-red-400"
                />
              </div>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 dark:text-white mb-6">
                The Legal Language Problem
              </h2>
              <p className="text-xl text-gray-600 dark:text-gray-300 max-w-4xl mx-auto mb-12">
                You shouldn't need a law degree to understand what you're
                signing. Legal consultation costs hundreds per hour, and most
                people skip reading important documents entirely.
              </p>
            </div>

            {/* Statistics */}
            <div className="grid md:grid-cols-3 gap-8 mb-16">
              {stats.map((stat, index) => (
                <div
                  key={index}
                  className="text-center bg-white dark:bg-gray-800 p-8 rounded-2xl shadow-lg"
                >
                  <div className="text-4xl sm:text-5xl font-bold text-blue-600 dark:text-blue-400 mb-2">
                    {stat.number}
                  </div>
                  <p className="text-gray-600 dark:text-gray-300 text-lg">
                    {stat.label}
                  </p>
                </div>
              ))}
            </div>

            {/* Solution Visual */}
            <div className="bg-white dark:bg-gray-800 rounded-3xl p-8 shadow-2xl border border-gray-200 dark:border-gray-700">
              <div className="grid lg:grid-cols-2 gap-12 items-center">
                <div>
                  <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
                    Before: Complex Legal Text
                  </h3>
                  <div className="bg-gray-100 dark:bg-gray-700 p-6 rounded-xl font-mono text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
                    "Notwithstanding any provision herein to the contrary, the
                    Party of the First Part hereby agrees to indemnify and hold
                    harmless the Party of the Second Part from and against any
                    and all claims, damages, losses, costs, and expenses..."
                  </div>
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
                    After: Plain English
                  </h3>
                  <div className="bg-green-50 dark:bg-green-900/20 p-6 rounded-xl border-l-4 border-green-500">
                    <div className="space-y-3 text-gray-700 dark:text-gray-300">
                      <div className="flex items-start gap-2">
                        <CheckCircle
                          size={20}
                          className="text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5"
                        />
                        <p>
                          <strong>You agree to:</strong> Pay for any damages or
                          legal costs if someone sues the other party because of
                          your actions
                        </p>
                      </div>
                      <div className="flex items-start gap-2">
                        <AlertTriangle
                          size={20}
                          className="text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5"
                        />
                        <p>
                          <strong>Risk:</strong> This could cost you significant
                          money if issues arise
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* How It Works */}
        <section id="how-it-works" className="py-20 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 dark:text-white mb-4">
                How It Works
              </h2>
              <p className="text-xl text-gray-600 dark:text-gray-300">
                Get instant legal document analysis in three simple steps
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              {[
                {
                  step: "01",
                  title: "Upload Document",
                  description:
                    "Simply drag and drop your legal document or paste the text directly into our secure platform.",
                },
                {
                  step: "02",
                  title: "AI Analysis",
                  description:
                    "Our advanced AI processes your document in seconds, identifying key terms, risks, and important clauses.",
                },
                {
                  step: "03",
                  title: "Get Insights",
                  description:
                    "Receive a clear, plain-English summary with highlighted risks, opportunities, and actionable recommendations.",
                },
              ].map((item, index) => (
                <div key={index} className="text-center relative">
                  <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-2xl font-bold w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg">
                    {item.step}
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                    {item.title}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                    {item.description}
                  </p>
                  {index < 2 && (
                    <div className="hidden md:block absolute top-8 left-16 w-full h-0.5 bg-gradient-to-r from-blue-600/50 to-indigo-600/50"></div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Final CTA Section */}
        <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-r from-blue-600 to-indigo-600">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-6">
              Ready to understand your legal documents?
            </h2>
            <p className="text-xl text-blue-100 mb-8">
              Join thousands of users who've simplified their legal document
              review process
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button className="bg-white text-blue-600 px-8 py-4 rounded-xl text-lg font-semibold shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200 flex items-center justify-center gap-2 group">
                Start Free Analysis
                <ArrowRight
                  size={20}
                  className="group-hover:translate-x-1 transition-transform"
                />
              </button>
              <button className="border-2 border-blue-200 text-white hover:bg-blue-200 hover:text-blue-600 px-8 py-4 rounded-xl text-lg font-semibold transition-all duration-200">
                Schedule Demo
              </button>
            </div>
            <p className="text-blue-200 text-sm mt-6">
              * No credit card required. Analysis completed in under 30 seconds.
            </p>
          </div>
        </section>

        {/* Footer */}
        <footer className="py-12 px-4 sm:px-6 lg:px-8 bg-gray-900 text-white">
          <div className="max-w-7xl mx-auto">
            <div className="grid md:grid-cols-4 gap-8">
              <div className="md:col-span-2">
                <div className="text-2xl font-bold mb-4">
                  Legal<span className="text-blue-400">AI</span> Docs
                </div>
                <p className="text-gray-400 mb-6 max-w-md">
                  Making legal documents accessible to everyone through advanced
                  AI technology. No law degree required.
                </p>
                <div className="flex gap-4">
                  <div className="bg-gray-800 p-2 rounded-lg">
                    <Shield size={20} className="text-blue-400" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold">Enterprise Security</p>
                    <p className="text-xs text-gray-400">
                      Your documents are processed securely and never stored
                    </p>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-semibold mb-4">Product</h4>
                <ul className="space-y-2 text-gray-400">
                  <li>
                    <a href="#" className="hover:text-white transition-colors">
                      Features
                    </a>
                  </li>
                  <li>
                    <a href="#" className="hover:text-white transition-colors">
                      How It Works
                    </a>
                  </li>
                  <li>
                    <a href="#" className="hover:text-white transition-colors">
                      Pricing
                    </a>
                  </li>
                  <li>
                    <a href="#" className="hover:text-white transition-colors">
                      API
                    </a>
                  </li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold mb-4">Support</h4>
                <ul className="space-y-2 text-gray-400">
                  <li>
                    <a href="#" className="hover:text-white transition-colors">
                      Help Center
                    </a>
                  </li>
                  <li>
                    <a href="#" className="hover:text-white transition-colors">
                      Contact Us
                    </a>
                  </li>
                  <li>
                    <a href="#" className="hover:text-white transition-colors">
                      Privacy Policy
                    </a>
                  </li>
                  <li>
                    <a href="#" className="hover:text-white transition-colors">
                      Terms of Service
                    </a>
                  </li>
                </ul>
              </div>
            </div>

            <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
              <p>&copy; 2025 LegalAI Docs. All rights reserved.</p>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}

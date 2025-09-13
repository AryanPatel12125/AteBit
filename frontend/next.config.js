/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable React Strict Mode for better development experience
  reactStrictMode: true,
  
  // Optimize images
  images: {
    domains: ['localhost'],
  },
  
  // Enable experimental features if needed
  experimental: {
    // Add any experimental features here
  },
};

module.exports = nextConfig;

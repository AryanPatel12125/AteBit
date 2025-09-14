/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable React Strict Mode for better development experience
  reactStrictMode: true,
  
  // Optimize images
  images: {
    domains: ['localhost'],
  },
  
  // Experimental features - turbo disabled for hot reload in Docker
  experimental: {
    // Keep turbo disabled to use webpack hot reload
  },
  
  // Hot reload configuration for Docker - use webpack with polling
  webpack: (config, { dev }) => {
    if (dev) {
      config.watchOptions = {
        poll: 1000,
        aggregateTimeout: 300,
        ignored: /node_modules/,
      }
    }
    return config
  },
};

module.exports = nextConfig;

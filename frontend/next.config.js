/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable React Strict Mode for better development experience
  reactStrictMode: true,
  
  // Optimize images
  images: {
    domains: ['localhost'],
  },
  
  // Development-specific configuration for Docker
  ...(process.env.NODE_ENV === 'development' && {
    // Enable file watching in Docker containers
    webpack: (config, { dev, isServer }) => {
      if (dev && !isServer) {
        // Enable polling for file changes in Docker
        config.watchOptions = {
          poll: 1000,
          aggregateTimeout: 300,
          ignored: /node_modules/,
        };
        
        // Optimize for development
        config.optimization = {
          ...config.optimization,
          removeAvailableModules: false,
          removeEmptyChunks: false,
          splitChunks: false,
        };
      }
      return config;
    },
  }),
  

  
  // Enable experimental features if needed
  experimental: {
    // Add any experimental features here
  },
};

module.exports = nextConfig;

# Use Node.js 18.18.0 exactly as specified  
FROM node:18.18.0-alpine

# Set working directory
WORKDIR /app

# Copy package files (both package.json and package-lock.json)
COPY package*.json ./

# Install ALL dependencies (including dev dependencies for development)
RUN npm ci

# Copy project files
COPY . .

# Expose port
EXPOSE 3000

# Start the development server with hot reloading
CMD ["npm", "run", "dev"]

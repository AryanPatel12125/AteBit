# Use Node.js 18.18.0 exactly as specified  
FROM node:18.18.0-alpine

# Set working directory
WORKDIR /app

# Copy package files (both package.json and package-lock.json)
COPY package*.json ./

# Install exact dependencies from lock file
RUN npm ci --omit=dev

# Copy project files
COPY . .

# Build the application
RUN npm run build

# Expose port
EXPOSE 3000

# Start the application
CMD ["npm", "start"]

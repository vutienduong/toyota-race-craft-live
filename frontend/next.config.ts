import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  // Disable experimental features that cause parsing issues
  experimental: {
    // Disable experimental type stripping - causes issues with async arrow functions
    typedRoutes: false,
  },
  typescript: {
    // Prevent Next.js from modifying tsconfig.json
    ignoreBuildErrors: false,
  },
  // Ensure webpack is used instead of experimental features
  webpack: (config) => {
    return config
  },
}

export default nextConfig

import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  // Configure Turbopack (empty config to silence warnings)
  turbopack: {},

  typescript: {
    // Let Next.js handle TypeScript configuration
    ignoreBuildErrors: false,
  },
}

export default nextConfig

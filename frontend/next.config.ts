import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  // Set Turbopack root to silence workspace detection warning
  experimental: {
    turbo: {
      root: '.',
    },
  },
}

export default nextConfig

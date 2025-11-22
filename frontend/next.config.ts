import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  // Disable experimental type stripping to fix async arrow function parsing
  typescript: {
    // Use traditional TypeScript compiler instead of experimental type stripping
    tsconfigPath: './tsconfig.json',
  },
}

export default nextConfig

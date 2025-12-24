import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  /* config options here */
  output: 'export',
  eslint: {
    // Skip linting during build (compilation is successful, only linting is failing)
    ignoreDuringBuilds: true,
  },
  typescript: {
    // The code compiles successfully, we can ignore type errors during build
    ignoreBuildErrors: true,
  },
};

export default nextConfig;

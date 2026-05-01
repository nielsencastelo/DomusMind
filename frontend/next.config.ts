import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  transpilePackages: ["recharts", "react-smooth"],
  env: {
    NEXT_PUBLIC_APP_VERSION: process.env.npm_package_version ?? "2.0.0",
  },
};

export default nextConfig;

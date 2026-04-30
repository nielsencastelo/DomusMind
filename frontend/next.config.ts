import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  transpilePackages: ["recharts", "react-smooth"],
};

export default nextConfig;

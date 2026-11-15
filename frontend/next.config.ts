import type { NextConfig } from "next";
import path from "path";

const common: NextConfig = {
  productionBrowserSourceMaps: true,
  // Removed standalone output for Azure App Service compatibility
  outputFileTracingRoot: path.join(__dirname, "../../"),
  experimental: {
    serverActions: {
      bodySizeLimit: "100mb",
    },
  },
  images: {
    domains: ["storage.googleapis.com"],
  },
};

const devConfig: NextConfig = {
  ...common,

  turbopack: {
    rules: {
      "*.svg": {
        loaders: ["@svgr/webpack"],
        as: "*.tsx",
      },
    },
  },
};

const prodConfig: NextConfig = {
  ...common,
  compiler: {
    ...common.compiler,
    removeConsole: true,
  },
  webpack: (config) => {
    config.module.rules.push({
      test: /\.svg$/,
      use: ["@svgr/webpack"],
    });

    config.resolve.alias["@"] = path.resolve(__dirname); // Set alias for the root directory

    return config;
  },
};

export default process.env.NODE_ENV === "development" ? devConfig : prodConfig;

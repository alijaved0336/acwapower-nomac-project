/* eslint-disable @typescript-eslint/no-require-imports */
const { createServer } = require("http");
const { parse } = require("url");
const next = require("next");
const path = require("path");
const fs = require("fs");

const dev = process.env.NODE_ENV !== "production";
const hostname = process.env.HOSTNAME || "0.0.0.0"; // Changed to 0.0.0.0 for Azure
const port = parseInt(process.env.PORT || "8080", 10); // Azure uses PORT 8080

// Verify .next directory exists
const nextDir = path.join(process.cwd(), ".next");

if (!fs.existsSync(nextDir)) {
  console.error(`API Error - .next directory not found at ${nextDir}`);
  console.error(
    "Please ensure the application is built before starting the server."
  );
  console.error("Run 'npm run build' to build the application.");
  process.exit(1);
}

// When using middleware `hostname` and `port` must be provided below
const app = next({
  dev,
  hostname,
  port,
  dir: process.cwd(),
});
const handle = app.getRequestHandler();

app
  .prepare()
  .then(() => {
    const server = createServer(async (req, res) => {
      try {
        // Health check endpoint for Azure
        if (req.url === "/health" || req.url === "/api/health") {
          res.writeHead(200, { "Content-Type": "application/json" });
          res.end(
            JSON.stringify({
              status: "ok",
              timestamp: new Date().toISOString(),
              mode: dev ? "development" : "production",
              nextDir: fs.existsSync(nextDir),
              cwd: process.cwd(),
            })
          );
          return;
        }

        // Be sure to pass `true` as the second argument to `url.parse`.
        // This tells it to parse the query portion of the URL.
        const parsedUrl = parse(req.url, true);
        await handle(req, res, parsedUrl);
      } catch (err) {
        console.error("API Error - Error handling request", req.url, err);
        res.statusCode = 500;
        res.end("internal server error");
      }
    });

    server.once("error", (err) => {
      console.error("API Error - Server error:", err);
      process.exit(1);
    });

    server.listen(port, hostname, () => {});

    // Graceful shutdown
    process.on("SIGTERM", () => {
      server.close(() => {
        process.exit(0);
      });
    });

    process.on("SIGINT", () => {
      server.close(() => {
        process.exit(0);
      });
    });
  })
  .catch((ex) => {
    console.error("API Error - Failed to start server:", ex);
    process.exit(1);
  });

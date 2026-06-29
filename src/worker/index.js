// Thin Cloudflare Worker that proxies every request to the FastAPI container.
// All real logic lives in the Python app (src/wfs/). This file should stay tiny.
import { Container, getContainer } from "@cloudflare/containers";

export class Backend extends Container {
  // Must match the port uvicorn listens on (see Dockerfile).
  defaultPort = 8000;
  // Spin the container down after this much idle time to save cost.
  sleepAfter = "5m";
}

export default {
  async fetch(request, env) {
    // Route everything to a single container instance for now.
    // TODO: shard by key/tenant via getContainer(env.BACKEND, <id>) if needed.
    const container = getContainer(env.BACKEND);
    return container.fetch(request);
  },
};

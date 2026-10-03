const API_BASE_URL = process.env.API_INTERNAL_URL || "http://127.0.0.1:8000";
const REQUEST_TIMEOUT_MS = 300_000;

export const maxDuration = 360;

async function proxyRequest(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  const target = new URL(
    path.map((segment) => encodeURIComponent(segment)).join("/"),
    `${API_BASE_URL.replace(/\/+$/, "")}/`,
  );
  target.search = new URL(request.url).search;

  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  const accept = request.headers.get("accept");
  if (contentType) headers.set("content-type", contentType);
  if (accept) headers.set("accept", accept);

  const method = request.method;
  const body = method === "GET" || method === "HEAD"
    ? undefined
    : await request.arrayBuffer();

  let upstream: Response;
  try {
    upstream = await fetch(target, {
      method,
      headers,
      body,
      cache: "no-store",
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
  } catch (error) {
    console.error("Backend API proxy request failed:", error);
    const timedOut = error instanceof Error && error.name === "TimeoutError";
    return Response.json(
      {
        detail: timedOut
          ? "The backend assessment timed out. Try again or use a smaller model."
          : "Could not reach the backend. Check that it is running on port 8000.",
      },
      { status: timedOut ? 504 : 502 },
    );
  }

  const responseHeaders = new Headers();
  const upstreamContentType = upstream.headers.get("content-type");
  if (upstreamContentType) {
    responseHeaders.set("content-type", upstreamContentType);
  }
  responseHeaders.set("cache-control", "no-store");

  return new Response(upstream.body, {
    status: upstream.status,
    headers: responseHeaders,
  });
}

export function GET(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
) {
  return proxyRequest(request, context);
}

export function POST(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
) {
  return proxyRequest(request, context);
}

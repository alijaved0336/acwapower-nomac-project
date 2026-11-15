// Commented out unused imports - uncomment when needed
// import { getSession } from "next-auth/react";
// import { auth } from "../../auth";

interface FetchAPIProps {
  url: string;
  method?: "GET" | "PUT" | "POST" | "DELETE" | "PATCH";
  body?: BodyInit | null;
  cache?: RequestCache;
  next?: NextFetchRequestConfig;
  includeHeaders?: boolean;
  externalHeaders?: HeadersInit;
  basePath?: string;
}

export async function fetchAPI<T>({
  url,
  method = "GET",
  body,
  cache = "no-store",
  next,

  includeHeaders = true,
  externalHeaders,
  basePath = "",
}: FetchAPIProps): Promise<T | undefined> {
  const { SERVER_URL } = process.env as Record<string, string>;
  // Commented out unused variable - uncomment when refresh functionality is implemented
  // const { AUTH_REFRESH_URL } = process.env as Record<string, string>;
  const endpoint = `${SERVER_URL}${basePath}${url}`;
  const requestStartTime = Date.now();
  const buildHeaders =
    async () // Commented out unused parameter - uncomment when auth is implemented
    // useAccessToken = true
    : Promise<HeadersInit> => {
      const headers: Record<string, string> = {
        ...(externalHeaders as Record<string, string>),
      };
      // const session = await auth();

      // if (includeHeaders && useAccessToken && session?.accessToken) {
      //   headers["Authorization"] = `Bearer ${session.accessToken}`;
      // }
      return headers;
    };

  const headers = await buildHeaders();
  const response = await fetch(url, {
    method,
    headers,
    body,
    cache,
    next,
  });

  // If access token expired, refresh and retry
  // if (response.status === 401 && AUTH_REFRESH_URL) {
  //   const session = await auth();

  //   if (session?.refreshToken) {
  //     await fetch(AUTH_REFRESH_URL, {
  //       method: "POST",
  //       headers: { "Content-Type": "application/json" },
  //       body: JSON.stringify({ refreshToken: session.refreshToken }),
  //     });

  //     // Retry original request with new access token
  //     headers = await buildHeaders();
  //     response = await fetch(endpoint, { method, headers, body, cache, next });
  //   }
  // }

  const duration = Date.now() - requestStartTime;

  try {
    const data = await response.json();

    if (response.ok) {
      // Enhanced logging for map-data endpoint
      if (url.includes("/map-data/")) {
      }
      return data as T;
    } else {
      console.error(
        `Dashboard Server API Error: ${method} ${url} - ${response.status} (${duration}ms)`,
        {
          status: response.status,
          statusText: response.statusText,
          error: data,
        }
      );
      return undefined;
    }
  } catch (parseError) {
    console.error(
      `Dashboard Server API Parse Error: ${method} ${url} - ${response.status} (${duration}ms)`,
      {
        status: response.status,
        statusText: response.statusText,
        parseError:
          parseError instanceof Error
            ? parseError.message
            : "Unknown parse error",
      }
    );
    return {} as T;
  }
}

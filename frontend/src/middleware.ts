// middleware.ts
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const protectedRoutes = ["/dashboard", "/profile"];
const authPageRoutes = ["/login"];
const apiAuthPrefix = "/api/auth";

// Check if user is authenticated via cookie
function isAuthenticated(req: NextRequest): boolean {
  const isAuthenticatedCookie = req.cookies.get("isAuthenticated");
  return isAuthenticatedCookie?.value === "true";
}

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  const isApiAuthRoute = pathname.startsWith(apiAuthPrefix);
  const isProtectedRoute = protectedRoutes.some((route) =>
    pathname.startsWith(route)
  );
  const isAuthPageRoute = authPageRoutes.includes(pathname);
  const isRootPage = pathname === "/";

  const userIsAuthenticated = isAuthenticated(req);

  // Allow API auth routes to pass through
  if (isApiAuthRoute) {
    return NextResponse.next();
  }

  // Handle root page navigation
  if (isRootPage) {
    if (userIsAuthenticated) {
      return NextResponse.redirect(
        new URL("/dashboard/plant-overview", req.url)
      );
    } else {
      return NextResponse.redirect(new URL("/login", req.url));
    }
  }

  // Protect dashboard routes - redirect to login if not authenticated
  if (isProtectedRoute && !userIsAuthenticated) {
    return NextResponse.redirect(new URL("/login", req.url));
  }

  // If authenticated user tries to access login page, redirect to plant-overview
  if (isAuthPageRoute && userIsAuthenticated) {
    return NextResponse.redirect(new URL("/dashboard/plant-overview", req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    "/((?!api|_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};

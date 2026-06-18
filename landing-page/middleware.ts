import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Lightweight gate for the /demo walkthrough.
 *
 * The demo is unlisted (not in nav or sitemap) and now also token-gated:
 *   - Share the link as  https://complisenseai.com/demo?key=<DEMO_ACCESS_TOKEN>
 *   - First visit with a valid ?key sets an httpOnly cookie and cleans the URL.
 *   - Subsequent visits are allowed via the cookie for 30 days.
 *   - Anyone without a valid key/cookie is redirected to the home page.
 *
 * The token is read server-side from DEMO_ACCESS_TOKEN and is never shipped
 * to the browser bundle. Set it in your host (Vercel) env. Falls back to a
 * dev default locally.
 */
const DEMO_TOKEN = process.env.DEMO_ACCESS_TOKEN ?? "complisense-demo";
const COOKIE_NAME = "cs_demo_access";

export function middleware(req: NextRequest) {
  const { pathname, searchParams } = req.nextUrl;
  if (!pathname.startsWith("/demo")) return NextResponse.next();

  // Already unlocked via cookie
  if (req.cookies.get(COOKIE_NAME)?.value === DEMO_TOKEN) {
    return NextResponse.next();
  }

  // Unlocking via ?key=... — set cookie and strip the key from the URL
  if (searchParams.get("key") === DEMO_TOKEN) {
    const cleanUrl = req.nextUrl.clone();
    cleanUrl.searchParams.delete("key");
    const res = NextResponse.redirect(cleanUrl);
    res.cookies.set(COOKIE_NAME, DEMO_TOKEN, {
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      path: "/demo",
      maxAge: 60 * 60 * 24 * 30, // 30 days
    });
    return res;
  }

  // Not authorised → send home
  const home = req.nextUrl.clone();
  home.pathname = "/";
  home.search = "";
  return NextResponse.redirect(home);
}

export const config = {
  matcher: ["/demo", "/demo/:path*"],
};

import { NextRequest, NextResponse } from "next/server";

// Demo-only "login": stores the chosen user id in a cookie.
export function GET(req: NextRequest) {
  const id = req.nextUrl.searchParams.get("id") ?? "";
  const res = NextResponse.redirect(new URL("/", req.url));
  res.cookies.set("user", id, { path: "/" });
  return res;
}

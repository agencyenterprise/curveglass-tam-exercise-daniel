import "./globals.css";
import Link from "next/link";
import type { ReactNode } from "react";
import { api } from "@/lib/api";
import { NAV } from "@/lib/nav";

export const metadata = { title: "Curveglass console (exercise)" };

export default async function RootLayout({ children }: { children: ReactNode }) {
  const [me, users] = await Promise.all([api.me(), api.users()]);
  return (
    <html lang="en">
      <body>
        <header>
          <Link href="/">Curveglass</Link>
          <nav>
            {NAV.filter((item) => item.roles.includes(me.role)).map((item) => (
              <Link key={item.href} href={item.href}>{item.label}</Link>
            ))}
          </nav>
          <div className="user">
            Signed in as <b>{me.name}</b> ({me.role}) · switch:
            {users.filter((u) => u.id !== me.id).map((u) => (
              <a key={u.id} href={`/switch-user?id=${u.id}`}>{u.name}</a>
            ))}
          </div>
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}

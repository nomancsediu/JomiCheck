import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans, Noto_Sans_Bengali } from "next/font/google";
import "./globals.css";
import { SiteFooter } from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { LangProvider } from "@/lib/i18n";

const plex = IBM_Plex_Sans({
  variable: "--font-plex",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

const bengali = Noto_Sans_Bengali({
  variable: "--font-bengali",
  subsets: ["bengali"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "JomiCheck — কেনার আগে যাচাই করুন",
  description:
    "Lawyer-grade pre-purchase land verification for citizens of Bangladesh: ownership, inheritance, mutation, litigation, khas, acquisition and fraud checks.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="bn" className={`${plex.variable} ${plexMono.variable} ${bengali.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <LangProvider>
          <SiteHeader />
          <main className="flex-1">{children}</main>
          <SiteFooter />
        </LangProvider>
      </body>
    </html>
  );
}

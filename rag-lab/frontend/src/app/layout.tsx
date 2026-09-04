import type { Metadata } from "next";
import { Poppins, Inter } from "next/font/google";
import "./globals.css";

const poppins = Poppins({
  variable: "--font-poppins",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  display: "swap",
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Nexara RAG",
  description:
    "Chat interface and retrieval evaluation dashboard for the local Nexara knowledge base.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    /* suppressHydrationWarning covers attributes that browser extensions
       inject into <html> before React hydrates, such as Night Eye adding
       nighteye="disabled". It applies to this element only, one level
       deep, so real mismatches inside the app still surface. */
    <html
      lang="en"
      className={`${poppins.variable} ${inter.variable} h-full`}
      suppressHydrationWarning
    >
      <body className="min-h-full">{children}</body>
    </html>
  );
}

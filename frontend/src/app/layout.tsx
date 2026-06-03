import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SafeRoute AI - Intelligent Navigation",
  description: "Smart navigation with safety scores, crime data, and environmental factors",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

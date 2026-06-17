import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ben's 40th · Rio Carnival 2027",
  description: "A private site for Ben's 40th birthday trip to Rio for Carnival 2027.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Space+Grotesk:wght@400;500;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body style={{ margin: 0, fontFamily: "'Space Grotesk', system-ui, sans-serif" }}>
        {children}
      </body>
    </html>
  );
}

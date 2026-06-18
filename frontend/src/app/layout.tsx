import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ResumeIQ — See your resume the way a recruiter does",
  description:
    "Upload or paste your resume. Get an explainable score, a recruiter's-eye view, and a line-by-line rewrite plan — before you apply.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}

import type { Metadata } from "next"
import { Inter, JetBrains_Mono, Pixelify_Sans } from "next/font/google"
import "./globals.css"
import { Sidebar } from "@/components/Sidebar"
import { getConversations } from "@/lib/api"

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-body",
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
})

const pixelifySans = Pixelify_Sans({
  subsets: ["latin"],
  variable: "--font-pixel",
})

export const metadata: Metadata = {
  title: "LLM Wiki",
  description: "Ingérez des documents et construisez un wiki structuré interrogeable par LLM.",
}

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const conversations = await getConversations()

  return (
    <html
      lang="fr"
      className={`${inter.variable} ${jetbrainsMono.variable} ${pixelifySans.variable} h-full`}
    >
      <body
        className="h-full flex antialiased"
        style={{ fontFamily: "var(--font-body), Inter, sans-serif" }}
      >
        <Sidebar conversations={conversations} />
        <main className="flex-1 h-full overflow-hidden">{children}</main>
      </body>
    </html>
  )
}

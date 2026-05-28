import { NextResponse } from "next/server"

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000"

export async function GET(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const res = await fetch(`${BACKEND}/wiki/history/${id}`, { cache: "no-store" })
  if (res.status === 404) return NextResponse.json({ error: "Introuvable" }, { status: 404 })
  const data = await res.json()
  return NextResponse.json(data)
}

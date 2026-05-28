import { NextResponse } from "next/server"

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000"

export async function GET() {
  const res = await fetch(`${BACKEND}/conversations`, { cache: "no-store" })
  const data = await res.json()
  return NextResponse.json(data, { status: res.status })
}

export async function POST() {
  const res = await fetch(`${BACKEND}/conversations`, { method: "POST" })
  const data = await res.json()
  return NextResponse.json(data, { status: res.status })
}

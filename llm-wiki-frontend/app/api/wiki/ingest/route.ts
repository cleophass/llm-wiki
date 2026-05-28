import { NextResponse } from "next/server"

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000"

export async function POST(req: Request) {
  const formData = await req.formData()
  const res = await fetch(`${BACKEND}/wiki/ingest`, {
    method: "POST",
    body: formData,
  })
  if (!res.ok) return NextResponse.json(null, { status: res.status })
  return NextResponse.json(await res.json())
}

export const runtime = 'nodejs';         // ensure Node runtime
export const dynamic = 'force-dynamic';  // no caching

function buildTarget(req: Request, path: string[]) {
  const u = new URL(req.url);
  const target = new URL(`${process.env.BACKEND_URL}/api/${path.join('/')}`);
  target.search = u.search; // keep query
  return target;
}

function hopByHop(h: string) {
  return ['connection','keep-alive','proxy-authenticate','proxy-authorization','te','trailer','transfer-encoding','upgrade','content-encoding'].includes(h.toLowerCase());
}

async function forward(req: Request, path: string[]) {
  const target = buildTarget(req, path);

  // Forward headers and add ngrok bypass
  const headers = new Headers(req.headers);
  headers.set('ngrok-skip-browser-warning', 'true');
  headers.set('User-Agent', 'sentinel-proxy'); // also disables the interstitial

  // Build init (only attach body when needed)
  const init: RequestInit = {
    method: req.method,
    headers,
    cache: 'no-store',
  };
  if (!['GET','HEAD'].includes(req.method)) {
    init.body = await req.arrayBuffer();
  }

  const r = await fetch(target, init);

  // Copy response headers (strip hop-by-hop)
  const outHeaders = new Headers();
  r.headers.forEach((v, k) => { if (!hopByHop(k)) outHeaders.set(k, v); });
  outHeaders.set('cache-control', 'no-store');

  return new Response(r.body, { status: r.status, headers: outHeaders });
}

export async function GET(req: Request, { params }: { params: { path: string[] } }) {
  return forward(req, params.path);
}
export async function POST(req: Request, ctx: any) { return forward(req, ctx.params.path); }
export async function PUT(req: Request, ctx: any)  { return forward(req, ctx.params.path); }
export async function DELETE(req: Request, ctx: any){ return forward(req, ctx.params.path); }
export async function OPTIONS(req: Request, ctx: any){ return forward(req, ctx.params.path); }

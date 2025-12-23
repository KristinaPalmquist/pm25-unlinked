export async function onRequest(context) {
  return new Response("hello from cloudflare", {
    headers: { "Content-Type": "text/plain" }
  });
}
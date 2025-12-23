export async function onRequest(context) {
  return new Response("ok", {
    headers: { "Content-Type": "text/plain" }
  });
}
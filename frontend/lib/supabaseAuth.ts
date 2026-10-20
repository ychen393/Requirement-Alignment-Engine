"use client";
const api = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
const key = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ?? "";
type Session = { access_token:string; refresh_token:string; expires_at:number; email?:string };
const slot = "rae-auth-session";
export const authConfigured = () => Boolean(api && key);
function read():Session|null {
  try {return JSON.parse(sessionStorage.getItem(slot) ?? "null") as Session|null;}
  catch {return null;}
}
async function call(path:string, payload:unknown, bearer?:string):Promise<any> {
  if (!authConfigured()) throw new Error("Supabase authentication not configured");
  const response = await fetch(api + "/auth/v1/" + path, {
    method:"POST", cache:"no-store",
    headers:{"Content-Type":"application/json", apikey:key,
      ...(bearer ? {Authorization:"Bearer " + bearer}: {})},
    body:JSON.stringify(payload),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error_description ?? data.msg ?? data.message ?? "Authentication failed");
  return data;
}
function persist(data:any):Session {
  if (!data.access_token || !data.refresh_token) throw new Error("Invalid authentication response");
  const session:Session = {
    access_token:data.access_token, refresh_token:data.refresh_token,
    expires_at:Math.floor(Date.now()/1000) + Number(data.expires_in ?? 3600),
    email:data.user?.email,
  };
  sessionStorage.setItem(slot,JSON.stringify(session));
  return session;
}
export async function signIn(email:string,password:string) {
  return persist(await call("token?grant_type=password",{email,password}));
}
export async function signUp(email:string,password:string) {
  return call("signup",{email,password});
}
export async function currentSession():Promise<Session|null> {
  const session=read();
  if (!session) return null;
  if (session.expires_at > Date.now()/1000 + 60) return session;
  try {return persist(await call("token?grant_type=refresh_token",{refresh_token:session.refresh_token}));}
  catch {sessionStorage.removeItem(slot);return null;}
}
export async function logOut() {
  const session=read();
  sessionStorage.removeItem(slot);
  if (session) {
    try {await call("logout",{},session.access_token);}
    catch {/* Local session is already cleared. */}
  }
}
export async function listKnowledge(organizationId:string) {
  const session=await currentSession();
  if (!session) throw new Error("Please log in first");
  const response=await fetch("/knowledge/documents?organization_id="+encodeURIComponent(organizationId),
    {headers:{Authorization:"Bearer "+session.access_token},cache:"no-store"});
  if(!response.ok)throw new Error("Knowledge request failed ("+response.status+")");
  return response.json() as Promise<Array<{id:string;title:string;kind:string}>>;
}

import { mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const cdpPort = process.env.CDP_PORT ?? "9222";
const origin = process.env.FRONTEND_URL ?? "http://localhost:3100";
const output = resolve("screenshots");
mkdirSync(output, { recursive: true });

const targets = await fetch(`http://127.0.0.1:${cdpPort}/json/list`).then((r) => r.json());
const target = targets.find((item) => item.type === "page");
if (!target) throw new Error("No Chrome page target found");

const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolveOpen, reject) => {
  socket.addEventListener("open", resolveOpen, { once: true });
  socket.addEventListener("error", reject, { once: true });
});

let id = 0;
const pending = new Map();
socket.addEventListener("message", (event) => {
  const message = JSON.parse(event.data);
  if (!message.id) return;
  const promise = pending.get(message.id);
  if (!promise) return;
  pending.delete(message.id);
  if (message.error) promise.reject(new Error(message.error.message));
  else promise.resolve(message.result);
});

function send(method, params = {}) {
  const messageId = ++id;
  socket.send(JSON.stringify({ id: messageId, method, params }));
  return new Promise((resolveSend, reject) => pending.set(messageId, { resolve: resolveSend, reject }));
}

async function evaluate(expression) {
  const result = await send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text);
  return result.result.value;
}

async function waitFor(expression, label, timeout = 30000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    if (await evaluate(`Boolean(${expression})`)) return;
    await new Promise((resolveWait) => setTimeout(resolveWait, 300));
  }
  throw new Error(`Timed out waiting for ${label}`);
}

async function navigate(path) {
  await send("Page.navigate", { url: `${origin}${path}` });
  await waitFor(`document.readyState === "complete"`, path);
  await new Promise((resolveWait) => setTimeout(resolveWait, 700));
}

async function clickText(text) {
  const encoded = JSON.stringify(text);
  const clicked = await evaluate(`(() => {
    const elements = [...document.querySelectorAll('button, a')];
    const element = elements.find((node) => node.textContent?.trim() === ${encoded})
      ?? elements.find((node) => node.textContent?.includes(${encoded}));
    if (!element) return false;
    element.click();
    return true;
  })()`);
  if (!clicked) throw new Error(`Could not find clickable text: ${text}`);
}

async function screenshot(name) {
  const result = await send("Page.captureScreenshot", {
    format: "png",
    captureBeyondViewport: true,
    fromSurface: true,
  });
  writeFileSync(resolve(output, name), Buffer.from(result.data, "base64"));
}

await send("Page.enable");
await send("Runtime.enable");

await navigate("/");
await evaluate(`sessionStorage.clear()`);
await send("Page.reload", { ignoreCache: true });
await waitFor(`document.readyState === "complete"`, "clean workbench");
await waitFor(`document.body.innerText.includes("让每一个需求")`, "workbench");
await screenshot("01-workbench.png");

await clickText("新建需求");
await waitFor(`location.pathname === "/new"`, "new requirement route");
await screenshot("02a-new-requirement-before-analysis.png");
await clickText("开始分析需求");
await waitFor(`document.body.innerText.includes("AI 初步分析")`, "AI analysis");
await screenshot("02-new-requirement-analysis.png");

await clickText("开始需求对齐");
await waitFor(`location.pathname === "/alignment" && document.body.innerText.includes("Requirement V1")`, "alignment workspace");
await screenshot("03-requirement-alignment.png");

await clickText("确认 Requirement V1");
await waitFor(`location.pathname === "/execution" && document.querySelector(".task-timeline")`, "execution plan");
await screenshot("04a-execution-v1-in-progress.png");
await clickText("记录需求变更");
await waitFor(`document.querySelector(".change-composer")`, "change composer");
await clickText("分析需求变更");
await waitFor(`document.body.innerText.includes("Requirement V1 → V2") && document.body.innerText.includes("新增任务")`, "change analysis");
await screenshot("04-execution-change-review.png");

await clickText("确认变更并更新执行计划");
await waitFor(`location.pathname === "/review" && document.body.innerText.includes("任务验收")`, "completion review");
await clickText("查看证据");
await clickText("确认验收结果");
await waitFor(`document.body.innerText.includes("用户已确认")`, "confirmed completion review");
await screenshot("05-completion-review.png");

const storedBeforeRefresh = await evaluate(`sessionStorage.getItem("requirement-alignment-session")`);
if (!storedBeforeRefresh) throw new Error("Workspace session state was not stored");
await send("Page.reload", { ignoreCache: true });
await waitFor(`document.readyState === "complete" && document.body.innerText.includes("任务验收")`, "review refresh");
const storedAfterRefresh = await evaluate(`sessionStorage.getItem("requirement-alignment-session")`);
if (storedAfterRefresh !== storedBeforeRefresh) throw new Error("Workspace session changed unexpectedly after refresh");

for (const path of ["/", "/new", "/alignment", "/execution", "/review"]) {
  await navigate(path);
  await waitFor(`!document.body.innerText.includes("无法加载")`, `${path} recovery state`);
}

await evaluate(`sessionStorage.clear()`);
await navigate("/review");
await waitFor(`document.body.innerText.includes("请先确认 Requirement V2 与修订计划")`, "missing-state recovery copy");
await evaluate(`sessionStorage.setItem("requirement-alignment-session", ${JSON.stringify(storedAfterRefresh)})`);
await navigate("/review");
await waitFor(`document.body.innerText.includes("任务验收")`, "restored review state");

console.log(JSON.stringify({
  screenshots: 7,
  workflow: "passed",
  sessionStorageRefresh: "passed",
  missingStateRecovery: "passed",
  routes: ["/", "/new", "/alignment", "/execution", "/review"],
}, null, 2));
socket.close();

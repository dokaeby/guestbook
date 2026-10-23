"use strict";
const $ = (id) => document.getElementById(id);
let page = 1;
let busy = false;
const storageKey = "small-guestbook-delete-keys";
let keys = {};
try { const saved = JSON.parse(localStorage.getItem(storageKey) || "{}"); if (saved && typeof saved === "object" && !Array.isArray(saved)) keys = saved; } catch { /* 저장소 차단 시에도 글 읽기는 가능합니다. */ }

function status(message, error = false) {
  $("status").textContent = message;
  $("status").classList.toggle("error", error);
}
function saveKeys() {
  try { localStorage.setItem(storageKey, JSON.stringify(keys)); return true; }
  catch { return false; }
}
async function api(url, options = {}) {
  const response = await fetch(url, options);
  if (response.status === 204) return null;
  const data = await response.json();
  if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "이름과 내용을 길이에 맞게 입력해 주세요.");
  return data;
}
function renderEntry(entry) {
  const article = document.createElement("article");
  article.className = "entry";
  const top = document.createElement("div"); top.className = "entry-top";
  const avatar = document.createElement("span"); avatar.className = "avatar"; avatar.textContent = Array.from(entry.name)[0]; avatar.setAttribute("aria-hidden", "true");
  const author = document.createElement("div");
  const name = document.createElement("span"); name.className = "entry-name"; name.textContent = entry.name;
  const date = document.createElement("time"); date.dateTime = entry.created_at;
  date.textContent = new Intl.DateTimeFormat("ko-KR", { dateStyle: "medium", timeStyle: "short" }).format(new Date(entry.created_at));
  author.append(name, date); top.append(avatar, author);
  if (typeof keys[entry.id] === "string") {
    const button = document.createElement("button"); button.type = "button"; button.className = "delete-button"; button.textContent = "내 글 삭제";
    button.addEventListener("click", async () => {
      if (!confirm("이 글을 삭제할까요?")) return;
      button.disabled = true;
      try {
        await api(`/api/entries/${entry.id}`, { method: "DELETE", headers: { Authorization: `Bearer ${keys[entry.id]}` } });
        delete keys[entry.id]; saveKeys(); await load(); status("글을 삭제했습니다.");
      } catch (error) { status(error.message || "연결을 확인해 주세요.", true); button.disabled = false; }
    });
    top.append(button);
  }
  const message = document.createElement("p"); message.className = "entry-message"; message.textContent = entry.message;
  article.append(top, message); return article;
}
async function load() {
  const data = await api(`/api/entries?page=${page}`);
  if (!data.items.length && page > 1) { page--; return load(); }
  const pages = Math.max(1, Math.ceil(data.total / data.page_size));
  $("total").textContent = `${data.total}개의 인사`;
  $("page-label").textContent = `${page} / ${pages}`;
  $("previous").disabled = page <= 1; $("next").disabled = page >= pages;
  $("entry-list").replaceChildren(...data.items.map(renderEntry));
  if (!data.items.length) {
    const empty = document.createElement("p"); empty.className = "empty"; empty.textContent = "아직 남겨진 인사가 없어요. 첫 번째 마음을 남겨 주세요."; $("entry-list").append(empty);
  }
}
$("message").addEventListener("input", () => { $("char-count").textContent = $("message").value.length; });
$("entry-form").addEventListener("submit", async (event) => {
  event.preventDefault(); if (busy) return;
  const name = $("name").value.trim(), message = $("message").value.trim();
  if (!name || !message) return status("이름과 내용을 입력해 주세요.", true);
  busy = true; $("submit-button").disabled = true;
  try {
    const entry = await api("/api/entries", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name, message }) });
    keys[entry.id] = entry.delete_token;
    // 저장된 오래된 삭제 키도 최대 1,000개만 유지합니다.
    const ids = Object.keys(keys).sort((a, b) => Number(b) - Number(a));
    for (const id of ids.slice(1000)) delete keys[id];
    const saved = saveKeys();
    $("message").value = ""; $("char-count").textContent = "0"; page = 1;
    status(saved ? "따뜻한 마음을 남겼습니다. 고마워요!" : "등록했습니다. 저장소가 차단되어 창을 닫으면 삭제 키가 사라집니다.");
    try { await load(); } catch { status("등록은 완료됐습니다. 목록을 보려면 새로고침해 주세요.", true); }
  } catch (error) { status(error.message || "연결을 확인해 주세요.", true); }
  finally { busy = false; $("submit-button").disabled = false; }
});
for (const [id, direction] of [["previous", -1], ["next", 1]]) {
  $(id).addEventListener("click", async () => {
    if (busy) return; busy = true; page += direction;
    try { await load(); status(""); } catch { page -= direction; status("목록을 불러오지 못했습니다. 다시 시도해 주세요.", true); }
    finally { busy = false; }
  });
}
load().catch(() => status("목록을 불러오지 못했습니다. 연결을 확인하고 새로고침해 주세요.", true));

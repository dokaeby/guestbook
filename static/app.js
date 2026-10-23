"use strict";

const $ = (id) => document.getElementById(id);
const storageKey = "small-guestbook-delete-keys";
let page = 1;
let pageCount = 1;
let busy = false;
let keys = {};

try {
  const saved = JSON.parse(localStorage.getItem(storageKey) || "{}");
  if (saved && typeof saved === "object" && !Array.isArray(saved)) keys = saved;
} catch { /* 저장소가 차단돼도 글 읽기와 등록은 가능합니다. */ }

function status(message, error = false) {
  $("status").textContent = message;
  $("status").classList.toggle("error", error);
}

function updateControls() {
  $("previous").disabled = busy || page <= 1;
  $("next").disabled = busy || page >= pageCount;
  $("submit-button").disabled = busy;
  for (const button of document.querySelectorAll(".delete-button, .retry-button")) {
    button.disabled = busy;
  }
}

function setBusy(value, submitting = false) {
  busy = value;
  const sending = value && submitting;
  $("entry-form").setAttribute("aria-busy", String(sending));
  $("submit-button").classList.toggle("is-loading", sending);
  $("submit-label").textContent = sending ? "남기는 중…" : "마음 남기기";
  // 전송 중에는 입력한 내용이 바뀌거나 사라지지 않게 합니다.
  $("name").readOnly = sending;
  $("message").readOnly = sending;
  updateControls();
}

function saveKeys() {
  try {
    localStorage.setItem(storageKey, JSON.stringify(keys));
    return true;
  } catch { return false; }
}

async function api(url, options = {}) {
  let response;
  try { response = await fetch(url, options); }
  catch { throw new Error("서버에 연결하지 못했습니다. 연결을 확인하고 다시 시도해 주세요."); }
  if (response.status === 204) return null;
  let data;
  try { data = await response.json(); }
  catch { throw new Error("서버 응답을 읽지 못했습니다. 잠시 후 다시 시도해 주세요."); }
  if (!response.ok) {
    throw new Error(typeof data.detail === "string" ? data.detail : "이름과 내용을 길이에 맞게 입력해 주세요.");
  }
  return data;
}

function renderEntry(entry) {
  const article = document.createElement("article");
  article.className = "entry";
  const top = document.createElement("div");
  top.className = "entry-top";
  const avatar = document.createElement("span");
  avatar.className = "avatar";
  avatar.textContent = Array.from(entry.name)[0];
  avatar.setAttribute("aria-hidden", "true");
  const author = document.createElement("div");
  author.className = "entry-author";
  const name = document.createElement("span");
  name.className = "entry-name";
  name.textContent = entry.name;
  const date = document.createElement("time");
  date.dateTime = entry.created_at;
  date.textContent = new Intl.DateTimeFormat("ko-KR", { dateStyle: "medium", timeStyle: "short" }).format(new Date(entry.created_at));
  author.append(name, date);
  top.append(avatar, author);

  if (typeof keys[entry.id] === "string") {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "delete-button";
    button.textContent = "내 글 삭제";
    button.setAttribute("aria-label", `${entry.name}님의 내 글 삭제`);
    button.addEventListener("click", async () => {
      if (busy || !confirm("이 글을 삭제할까요?")) return;
      setBusy(true);
      button.textContent = "삭제 중…";
      try {
        await api(`/api/entries/${entry.id}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${keys[entry.id]}` },
        });
        delete keys[entry.id];
        saveKeys();
        try {
          await load();
          status("글을 삭제했습니다.");
        } catch {
          // 삭제가 완료된 글을 재시도하지 않도록 화면에서도 제거합니다.
          article.remove();
          status("글을 삭제했습니다. 최신 목록을 보려면 새로고침해 주세요.", true);
        }
      } catch (error) {
        status(error.message, true);
      } finally {
        button.textContent = "내 글 삭제";
        setBusy(false);
      }
    });
    top.append(button);
  }

  const message = document.createElement("p");
  message.className = "entry-message";
  message.textContent = entry.message;
  article.append(top, message);
  return article;
}

function emptyState(title, description) {
  const empty = document.createElement("div");
  empty.className = "empty";
  const heading = document.createElement("strong");
  heading.textContent = title;
  const text = document.createElement("p");
  text.textContent = description;
  empty.append(heading, text);
  return empty;
}

async function load() {
  $("entry-list").setAttribute("aria-busy", "true");
  try {
    const data = await api(`/api/entries?page=${page}`);
    pageCount = Math.max(1, Math.ceil(data.total / data.page_size));
    if (page > pageCount) {
      page = pageCount;
      return await load();
    }
    $("total").textContent = `${data.total}개의 인사`;
    $("page-label").textContent = `${page} / ${pageCount}`;
    $("entry-list").replaceChildren(...data.items.map(renderEntry));
    if (!data.items.length) {
      $("entry-list").append(emptyState(
        "첫 번째 인사를 기다리고 있어요",
        "아직 남겨진 인사가 없어요. 당신의 따뜻한 한 줄로 시작해 주세요.",
      ));
    }
    updateControls();
  } finally {
    $("entry-list").setAttribute("aria-busy", "false");
  }
}

function showListError() {
  $("total").textContent = "연결 확인";
  const empty = emptyState("인사를 불러오지 못했어요", "연결을 확인한 뒤 다시 시도해 주세요.");
  const retry = document.createElement("button");
  retry.type = "button";
  retry.className = "retry-button";
  retry.textContent = "다시 불러오기";
  retry.addEventListener("click", refresh);
  empty.append(retry);
  $("entry-list").replaceChildren(empty);
}

async function refresh() {
  if (busy) return;
  setBusy(true);
  try {
    await load();
  } catch {
    showListError();
  } finally {
    setBusy(false);
  }
}

$("message").addEventListener("input", () => {
  $("char-count").textContent = $("message").value.length;
});

$("entry-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (busy) return;
  const name = $("name").value.trim();
  const message = $("message").value.trim();
  if (!name || !message) {
    status("이름과 내용을 입력해 주세요.", true);
    (!name ? $("name") : $("message")).focus();
    return;
  }
  setBusy(true, true);
  status("");
  try {
    const entry = await api("/api/entries", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, message }),
    });
    keys[entry.id] = entry.delete_token;
    // 저장된 오래된 삭제 키도 최대 1,000개만 유지합니다.
    const ids = Object.keys(keys).sort((a, b) => Number(b) - Number(a));
    for (const id of ids.slice(1000)) delete keys[id];
    const saved = saveKeys();
    $("message").value = "";
    $("char-count").textContent = "0";
    page = 1;
    status(saved ? "따뜻한 마음을 남겼습니다. 고마워요!" : "등록했습니다. 저장소가 차단되어 창을 닫으면 삭제 키가 사라집니다.");
    try { await load(); }
    catch { status("등록은 완료됐습니다. 목록을 보려면 새로고침해 주세요.", true); }
  } catch (error) {
    status(error.message, true);
  } finally {
    setBusy(false);
  }
});

for (const [id, direction] of [["previous", -1], ["next", 1]]) {
  $(id).addEventListener("click", async () => {
    if (busy) return;
    const previousPage = page;
    page += direction;
    setBusy(true);
    try { await load(); }
    catch {
      page = previousPage;
      status("목록을 불러오지 못했습니다. 다시 시도해 주세요.", true);
    } finally {
      setBusy(false);
    }
  });
}

refresh();

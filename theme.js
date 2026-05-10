// CORIN Dashboard v2 — 時計 / モード切替 / カウントダウン / 紙吹雪 / イースターエッグ

(function() {
  const now = new Date();
  const y = now.getFullYear();
  const m = now.getMonth() + 1;
  const d = now.getDate();
  const w = now.getDay();
  const pad = (n) => n.toString().padStart(2, '0');

  // ======== 日付表示 ========
  const wkLabel = ['日', '月', '火', '水', '木', '金', '土'][w];
  document.getElementById('date-main').textContent = `${y}-${pad(m)}-${pad(d)}`;
  document.getElementById('date-week').textContent = `（${wkLabel}）`;

  // ======== 時計（1分更新・JSTで現在の手元時刻） ========
  function updateClock() {
    const t = new Date();
    document.getElementById('clock').textContent = `${pad(t.getHours())}:${pad(t.getMinutes())}`;
  }
  updateClock();
  setInterval(updateClock, 30 * 1000);

  // ======== テーマタグ（曜日感だけシンプルに） ========
  let themeTag = '— 朝の3分 —';
  if (w === 0 || w === 6) themeTag = '🎀 週末モード';
  else if (w === 1) themeTag = '🍵 月曜・今週の3つ';
  else if (w === 5) themeTag = '🌙 金曜・整理の日';
  document.getElementById('theme-tag').textContent = themeTag;

  // ======== モード切替（localStorage / デフォルトは仕事） ========
  const body = document.body;
  const switchEl = document.getElementById('mode-switch');
  const SAVED = localStorage.getItem('corin-mode'); // 'work' or 'private'
  const initialMode = SAVED || 'work';
  applyMode(initialMode);
  switchEl.checked = (initialMode === 'private');

  switchEl.addEventListener('change', () => {
    const next = switchEl.checked ? 'private' : 'work';
    applyMode(next);
    localStorage.setItem('corin-mode', next);
    if (next === 'private') {
      // プライベートに切替えた瞬間にちょっとだけ紙吹雪
      sprinkleConfetti(20);
    }
  });

  function applyMode(mode) {
    body.classList.remove('mode-work', 'mode-private');
    body.classList.add(`mode-${mode}`);
  }

  // ======== カウントダウン（一番近い未来のイベントを表示） ========
  // 5/9 結婚式は過ぎたので除外（過去日は自動スキップ）
  const events = [
    { md: '05-23', label: '🤵 葉月ちゃん結婚式' },
    { md: '03-12', label: '🎂 ゆりこの誕生日' },
    { md: '12-25', label: '🎄 クリスマス' },
    { md: '01-01', label: '🎍 お正月' },
  ];
  // 毎月28日 MEADOW. Magazine
  events.push({ md: monthlyMagazineDate(), label: '🦋 MEADOW. Magazine' });

  const today0 = new Date(y, m - 1, d);
  let bestDiff = Infinity, bestEvent = null;
  for (const ev of events) {
    if (!ev.md) continue;
    const [em, ed] = ev.md.split('-').map(Number);
    let target = new Date(y, em - 1, ed);
    if (target < today0) target = new Date(y + 1, em - 1, ed);
    const diff = Math.round((target - today0) / 86400000);
    if (diff < bestDiff) { bestDiff = diff; bestEvent = ev; }
  }
  if (bestEvent) {
    document.getElementById('countdown-label').textContent = bestEvent.label;
    document.getElementById('countdown-days').textContent = bestDiff;
  }

  function monthlyMagazineDate() {
    // 今月28日が未来 → 今月28日 / 過ぎてたら来月28日
    const this28 = new Date(y, m - 1, 28);
    if (this28 >= today0) return `${pad(m)}-28`;
    const next = new Date(y, m, 28);
    return `${pad(next.getMonth() + 1)}-28`;
  }

  // ======== AI/Fashion リンクURL組み立て ========
  const todayStr = `${y}-${pad(m)}-${pad(d)}`;
  const aiLink = document.getElementById('ai-link');
  const fashionLink = document.getElementById('fashion-link');
  if (aiLink) aiLink.href = `https://fujimoto-cpu.github.io/x-ai-trends/${todayStr}.html`;
  if (fashionLink) fashionLink.href = `https://fujimoto-cpu.github.io/fashion-report/${todayStr}.html`;

  // ======== data.js 流し込み ========
  if (typeof window.CORIN_DATA !== 'undefined') {
    fillDynamicData(window.CORIN_DATA);
  }

  function fillDynamicData(data) {
    // 天気ミニ表示
    if (data.weather) {
      document.getElementById('weather-mini').textContent =
        `${data.weather.icon || '☁️'} ${data.weather.temp}℃ ${data.weather.desc || ''}`;
    }
    // CORIN手紙
    if (data.letter) {
      const lb = document.getElementById('letter-body');
      const ascii = document.getElementById('letter-ascii');
      if (data.letter.ascii) ascii.textContent = data.letter.ascii;
      if (data.letter.html) lb.innerHTML = data.letter.html;
    }
    if (data.ai && data.ai.summary) document.getElementById('ai-summary').innerHTML = data.ai.summary;
    if (data.fashion && data.fashion.summary) document.getElementById('fashion-summary').innerHTML = data.fashion.summary;
    if (data.trend && data.trend.summary) document.getElementById('trend-summary').innerHTML = data.trend.summary;
    if (data.xwatch && data.xwatch.summary) document.getElementById('xwatch-summary').innerHTML = data.xwatch.summary;

    // ブランド
    if (data.brand) {
      const img = document.getElementById('brand-image');
      const name = document.getElementById('brand-name');
      const tagline = document.getElementById('brand-tagline');
      const insight = document.getElementById('brand-insight');
      const link = document.getElementById('brand-link');
      if (data.brand.image_url) img.innerHTML = `<img src="${data.brand.image_url}" alt="${data.brand.name}">`;
      if (data.brand.name) name.textContent = data.brand.name;
      if (data.brand.tagline) tagline.textContent = data.brand.tagline;
      if (data.brand.insight) insight.textContent = data.brand.insight;
      if (data.brand.local_path) {
        link.href = `obsidian://advanced-uri?vault=corin&filepath=${encodeURIComponent(data.brand.local_path)}&openmode=tab`;
      }
    }

    if (data.ip && data.ip.url) document.getElementById('ip-link').href = data.ip.url;

    // MEADOW.
    if (data.meadow && data.meadow.summary) {
      const meadowSummary = document.getElementById('meadow-summary');
      if (meadowSummary) meadowSummary.innerHTML = data.meadow.summary.replace(/  \/  /g, '<br>');
    }

    // 推し画像（/collection 連携）
    if (data.oshi) renderOshi(data.oshi);

    // 今夜の楽しみ
    if (data.tonight) renderTonight(data.tonight);

    // 今日の一枚
    if (data.daily_photo) renderDailyPhoto(data.daily_photo);

    // コレクション統計
    if (data.collection_stats) renderCollectionStats(data.collection_stats);
  }

  function renderOshi(oshi) {
    const wrap = document.getElementById('oshi-content');
    if (!oshi || !oshi.image) return;
    const caption = oshi.caption || oshi.category_label || '';
    const title = oshi.title || '';
    wrap.innerHTML = `
      <img class="oshi-image" src="${oshi.image}" alt="${title}">
      <div class="oshi-meta">
        <p class="oshi-caption">${title ? `<strong>${title}</strong> — ` : ''}${caption}</p>
      </div>`;
  }

  function renderTonight(tonight) {
    if (!tonight || !tonight.summary) return;
    const sec = document.getElementById('tonight-section');
    sec.style.display = '';
    const text = document.getElementById('tonight-text');
    text.innerHTML = `<span class="tonight-time">${tonight.time || ''}</span>${tonight.summary}`;
  }

  function renderDailyPhoto(photo) {
    if (!photo || !photo.image) return;
    const sec = document.getElementById('polaroid-section');
    sec.style.display = '';
    const wrap = document.getElementById('polaroid-wrap');
    wrap.innerHTML = `
      <a class="polaroid" href="${photo.link || '#'}" target="_blank">
        <img src="${photo.image}" alt="${photo.caption || ''}">
        <p class="polaroid-caption">${photo.caption || todayStr}</p>
      </a>`;
  }

  function renderCollectionStats(stats) {
    const wrap = document.getElementById('coll-stats');
    if (!stats || !stats.categories) return;
    const max = Math.max(1, ...stats.categories.map(c => c.count));
    const rows = stats.categories.map(c => `
      <div class="coll-stat-row">
        <span class="coll-stat-label">${c.label}</span>
        <div class="coll-stat-bar"><div class="coll-stat-fill" style="width:${(c.count / max) * 100}%"></div></div>
        <span class="coll-stat-count">${c.count}</span>
      </div>`).join('');
    wrap.innerHTML = rows + `<p class="coll-total">今月合計：${stats.total} 件</p>`;
  }

  // ======== 朝のチェックリスト（手動・localStorage） ========
  const TODO_KEY = `corin-todo-${todayStr}`;
  let todos = JSON.parse(localStorage.getItem(TODO_KEY) || '[]');
  const todoListEl = document.getElementById('todo-list');
  const todoInputEl = document.getElementById('todo-input');
  const todoAddBtn = document.getElementById('todo-add-btn');

  function renderTodos() {
    todoListEl.innerHTML = todos.map((t, i) => `
      <li class="${t.done ? 'done' : ''}">
        <input type="checkbox" class="todo-checkbox" data-i="${i}" ${t.done ? 'checked' : ''}>
        <span>${escapeHtml(t.text)}</span>
        <button class="todo-delete" data-del="${i}">×</button>
      </li>`).join('');
  }

  function saveTodos() { localStorage.setItem(TODO_KEY, JSON.stringify(todos)); }

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  todoAddBtn.addEventListener('click', addTodo);
  todoInputEl.addEventListener('keydown', e => { if (e.key === 'Enter') addTodo(); });

  function addTodo() {
    const text = todoInputEl.value.trim();
    if (!text) return;
    if (todos.length >= 3) {
      todoInputEl.value = '';
      todoInputEl.placeholder = '3つまでにしよ！';
      setTimeout(() => { todoInputEl.placeholder = '例: メール返信3件'; }, 1500);
      return;
    }
    todos.push({ text, done: false });
    todoInputEl.value = '';
    saveTodos();
    renderTodos();
  }

  todoListEl.addEventListener('click', (e) => {
    const cb = e.target.closest('.todo-checkbox');
    const del = e.target.closest('.todo-delete');
    if (cb) {
      const i = +cb.dataset.i;
      todos[i].done = cb.checked;
      saveTodos();
      renderTodos();
      if (cb.checked) sprinkleConfetti(40);
    } else if (del) {
      const i = +del.dataset.del;
      todos.splice(i, 1);
      saveTodos();
      renderTodos();
    }
  });
  renderTodos();

  // ======== 紙吹雪 ========
  const CONFETTI_COLORS = ['#f08c7a', '#4a9be8', '#3fa86a', '#c8b6e2', '#e8c4d0', '#b8c9a4'];
  function sprinkleConfetti(count = 30) {
    for (let i = 0; i < count; i++) {
      const el = document.createElement('div');
      el.className = 'confetti';
      el.style.left = Math.random() * 100 + 'vw';
      el.style.top = '-20px';
      el.style.background = CONFETTI_COLORS[Math.floor(Math.random() * CONFETTI_COLORS.length)];
      el.style.animationDelay = (Math.random() * 0.3) + 's';
      el.style.animationDuration = (0.8 + Math.random() * 0.6) + 's';
      document.body.appendChild(el);
      setTimeout(() => el.remove(), 1800);
    }
  }
  window.sprinkleConfetti = sprinkleConfetti; // デバッグ用

  // ======== イースターエッグ：CORINロゴ・トリプルクリック ========
  const EGG_ASCII = [
    " /) /)\n(  • •)\n⊃ 💐",
    " /)/) ˚｡´☆\n( . .) ☆´˚｡\n⊃  ❤️ ☆",
    "  (\\(\\\n(o- .•)❤️\no_(\")(\" )",
    "  n__n\n  ={ >⩊< }=\n  ~/…•🌹•",
    " /)/)\n( ≧ ▽≦)\n⊃  🎶",
  ];
  const EGG_MESSAGES = [
    "やっほー！見つけてくれてありがと🎀",
    "ゆりこ、今日も一緒にいこう！",
    "ちゃんと休憩してる？水飲んで〜",
    "70%でいいんだよ、完璧じゃなくて。",
    "好きなもの集めるの忘れないでね💐",
    "今日のゆりこ、最高にかわいい",
  ];
  const logo = document.getElementById('corin-logo');
  let clickTimes = [];
  if (logo) {
    logo.addEventListener('click', () => {
      const now = Date.now();
      clickTimes.push(now);
      clickTimes = clickTimes.filter(t => now - t < 1500);
      if (clickTimes.length >= 3) {
        clickTimes = [];
        showEgg();
      }
    });
  }
  function showEgg() {
    const ex = document.querySelector('.egg-popup');
    if (ex) ex.remove();
    const ascii = EGG_ASCII[Math.floor(Math.random() * EGG_ASCII.length)];
    const msg = EGG_MESSAGES[Math.floor(Math.random() * EGG_MESSAGES.length)];
    const pop = document.createElement('div');
    pop.className = 'egg-popup';
    pop.innerHTML = `<div class="egg-ascii">${ascii}</div><div>${msg}</div>`;
    document.body.appendChild(pop);
    sprinkleConfetti(50);
    setTimeout(() => pop.remove(), 4000);
  }
})();

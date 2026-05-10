// CORIN Dashboard — 色テーマ自動変化＋日付表示＋データ流し込み

(function() {
  const now = new Date();
  const y = now.getFullYear();
  const m = now.getMonth() + 1; // 1-12
  const d = now.getDate();
  const w = now.getDay(); // 0=日, 6=土

  // --- 日付表示 ---
  const wkLabel = ['日', '月', '火', '水', '木', '金', '土'][w];
  const pad = (n) => n.toString().padStart(2, '0');
  document.getElementById('date-main').textContent = `${y}-${pad(m)}-${pad(d)}`;
  document.getElementById('date-week').textContent = `（${wkLabel}）`;

  // --- 色テーマ判定（優先順位：特別日 > 季節 > 週末 > デフォルト平日） ---
  const body = document.body;
  let theme = 'weekday';
  let themeTag = '— 朝の3分 —';

  // 季節判定
  if (m >= 3 && m <= 5) { theme = 'spring'; themeTag = '🌸 春の朝'; }
  else if (m >= 6 && m <= 8) { theme = 'summer'; themeTag = '🌊 夏の朝'; }
  else if (m >= 9 && m <= 11) { theme = 'autumn'; themeTag = '🍁 秋の朝'; }
  else { theme = 'winter'; themeTag = '❄️ 冬の朝'; }

  // 週末は季節を上書き（ピンク優位）
  if (w === 0 || w === 6) {
    theme = 'weekend';
    themeTag = '🎀 週末モード';
  }

  // 特別日（友達結婚式・誕生日など）
  const specialDays = [
    { md: '05-09', tag: '💒 結婚式の日' },
    { md: '03-12', tag: '🎂 ゆりこの誕生日' },
  ];
  const todayMd = `${pad(m)}-${pad(d)}`;
  for (const sd of specialDays) {
    if (sd.md === todayMd) {
      theme = 'special';
      themeTag = sd.tag;
      break;
    }
  }

  body.classList.add(`theme-${theme}`);
  document.getElementById('theme-tag').textContent = themeTag;

  // --- リンクURL組み立て（既存リポの当日HTMLへ） ---
  const todayStr = `${y}-${pad(m)}-${pad(d)}`;
  const aiLink = document.getElementById('ai-link');
  const fashionLink = document.getElementById('fashion-link');
  if (aiLink) aiLink.href = `https://fujimoto-cpu.github.io/x-ai-trends/${todayStr}.html`;
  if (fashionLink) fashionLink.href = `https://fujimoto-cpu.github.io/fashion-report/${todayStr}.html`;

  // --- data.js 読み込み（Phase 2の動的データ） ---
  // window.CORIN_DATA = { letter, ai, fashion, trend, xwatch, brand, ip } の形で来る前提
  if (typeof window.CORIN_DATA !== 'undefined') {
    fillDynamicData(window.CORIN_DATA);
  } else {
    // data.js がまだ無い場合は静的プレースホルダーのまま
    console.log('[CORIN] data.js not loaded yet — static placeholder mode');
  }

  function fillDynamicData(data) {
    // CORIN手紙
    if (data.letter) {
      const body = document.getElementById('letter-body');
      const ascii = document.getElementById('letter-ascii');
      if (data.letter.ascii) ascii.textContent = data.letter.ascii;
      if (data.letter.html) body.innerHTML = data.letter.html;
    }
    // AIサマリー
    if (data.ai && data.ai.summary) {
      document.getElementById('ai-summary').innerHTML = data.ai.summary;
    }
    // ファッション
    if (data.fashion && data.fashion.summary) {
      document.getElementById('fashion-summary').innerHTML = data.fashion.summary;
    }
    // トレンドダイジェスト
    if (data.trend && data.trend.summary) {
      document.getElementById('trend-summary').innerHTML = data.trend.summary;
    }
    // X Watch
    if (data.xwatch && data.xwatch.summary) {
      document.getElementById('xwatch-summary').innerHTML = data.xwatch.summary;
    }
    // ブランド分析
    if (data.brand) {
      const img = document.getElementById('brand-image');
      const name = document.getElementById('brand-name');
      const tagline = document.getElementById('brand-tagline');
      const insight = document.getElementById('brand-insight');
      const link = document.getElementById('brand-link');
      if (data.brand.image_url) {
        img.innerHTML = `<img src="${data.brand.image_url}" alt="${data.brand.name}">`;
      }
      if (data.brand.name) name.textContent = data.brand.name;
      if (data.brand.tagline) tagline.textContent = data.brand.tagline;
      if (data.brand.insight) insight.textContent = data.brand.insight;
      if (data.brand.local_path) {
        const encoded = encodeURIComponent(data.brand.local_path);
        link.href = `obsidian://advanced-uri?vault=corin&filepath=${encoded}&openmode=tab`;
      }
    }
    // IP
    if (data.ip && data.ip.url) {
      document.getElementById('ip-link').href = data.ip.url;
    }
  }
})();

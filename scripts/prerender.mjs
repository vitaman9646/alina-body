// Генерация статического HTML для блога и мини-курсов (prerender).
// Запускается после vite build: создаёт dist/blog/{slug}/index.html и
// dist/tonus-doma/index.html — их видят поисковики без JS (Яндекс и др.).
import { writeFileSync, mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';

const SITE_URL = 'https://alina-body.fitness';
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.VITE_SUPABASE_URL;
const ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.VITE_SUPABASE_ANON_KEY;

if (!SUPABASE_URL || !ANON_KEY) {
  console.error('prerender: нет SUPABASE_URL / ANON_KEY в env — пропускаю');
  process.exit(0);
}

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function absUrl(u) {
  if (!u) return null;
  if (/^https?:\/\//.test(u)) return u;
  return SITE_URL + (u.startsWith('/') ? u : '/' + u);
}

const CSS = `
  * { box-sizing: border-box; }
  body { margin: 0; background: #FBF7F2; color: #3A312C; font-family: -apple-system, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; }
  .wrap { max-width: 720px; margin: 0 auto; padding: 32px 20px 64px; }
  .logo { font-size: 20px; font-weight: 700; color: #3A312C; text-decoration: none; }
  .logo em { font-style: normal; font-weight: 400; }
  nav a { color: #8A7B73; text-decoration: none; margin-right: 16px; font-size: 14px; }
  nav { margin: 12px 0 24px; }
  h1 { font-size: 32px; line-height: 1.15; margin: 0 0 16px; }
  .meta { color: #8A7B73; font-size: 14px; margin-bottom: 24px; }
  .content { font-size: 17px; }
  .content p { margin: 0 0 16px; }
  .content img { max-width: 100%; height: auto; border-radius: 12px; }
  .cover { width: 100%; border-radius: 16px; margin-bottom: 24px; }
  .cta { margin-top: 32px; padding: 20px; background: #F3EBE3; border-radius: 14px; }
  .cta a { color: #3A312C; font-weight: 600; }
  .card { border: 1px solid #eee5dc; border-radius: 14px; padding: 18px; margin-bottom: 16px; background: #fff; }
  .card h2 { margin: 0 0 8px; font-size: 20px; }
  .price { font-weight: 700; }
`;

function page({ title, description, canonical, image, type = 'website', jsonLd = [], body }) {
  const img = absUrl(image) || `${SITE_URL}/images/hero-alina.jpg`;
  const ld = (jsonLd || []).map((o) => `<script type="application/ld+json">${JSON.stringify(o)}</script>`).join('\n');
  return `<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)}</title>
<meta name="description" content="${esc(description)}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<link rel="canonical" href="${canonical}">
<meta property="og:type" content="${type}">
<meta property="og:site_name" content="Alina Body">
<meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(description)}">
<meta property="og:url" content="${canonical}">
<meta property="og:image" content="${img}">
<meta name="twitter:card" content="summary_large_image">
${ld}
<style>${CSS}</style>
</head>
<body>
<div class="wrap">
<a class="logo" href="${SITE_URL}/">Alina <em>Body</em></a>
<nav><a href="${SITE_URL}/">Главная</a><a href="${SITE_URL}/tonus-doma">Мини-курсы</a><a href="${SITE_URL}/blog">Блог</a></nav>
${body}
</div>
</body>
</html>`;
}

function renderPost(p) {
  const canonical = `${SITE_URL}/blog/${p.slug}`;
  const cover = p.cover_image ? `<img class="cover" src="${esc(absUrl(p.cover_image))}" alt="${esc(p.title)}">` : '';
  const date = p.published_at ? new Date(p.published_at).toLocaleDateString('ru-RU', { year: 'numeric', month: 'long', day: 'numeric' }) : '';
  const jsonLd = [{
    '@context': 'https://schema.org',
    '@type': 'BlogPosting',
    headline: p.title,
    description: p.excerpt || '',
    image: p.cover_image ? [absUrl(p.cover_image)] : [],
    datePublished: p.published_at,
    author: { '@type': 'Organization', name: 'Alina Body' },
    publisher: { '@type': 'Organization', name: 'Alina Body' },
    mainEntityOfPage: canonical,
  }];
  const body = `
<article>
<h1>${esc(p.title)}</h1>
${date ? `<div class="meta">${esc(date)}</div>` : ''}
${cover}
<div class="content">${p.content || ''}</div>
<div class="cta">Хочешь продолжить? <a href="${SITE_URL}/tonus-doma">Выбрать мини-курс →</a></div>
</article>`;
  return page({ title: `${p.title} — Alina Body`, description: p.excerpt || p.title, canonical, image: p.cover_image, type: 'article', jsonLd, body });
}

function renderMiniCourses(themes) {
  const canonical = `${SITE_URL}/tonus-doma`;
  const cards = (themes || []).map((t) => `
<div class="card">
<h2>${esc(t.title)}</h2>
<p>Трипваер «${esc(t.tripwire_title)}» — ${t.tripwire_days} дня, ${t.tripwire_minutes_per_day} минут в день, <span class="price">${Number(t.tripwire_price) || 0} ₽</span></p>
<p>Полная программа: ${esc(t.course_title)} — ${t.course_days} дней, <span class="price">${Number(t.course_price) || 0} ₽</span></p>
</div>`).join('\n');
  const jsonLd = [{
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: 'Мини-курсы Alina Body',
    description: 'Короткие домашние мини-курсы по зонам тела: 3–7 дней, 15–20 минут в день.',
    url: canonical,
  }];
  const body = `
<h1>Мини-курсы</h1>
<p class="meta">Короткие программы под свою цель — начните с малого шага.</p>
${cards || '<p>Мини-курсы скоро появятся.</p>'}`;
  return page({ title: 'Мини-курсы — Alina Body', description: 'Короткие домашние мини-курсы по зонам тела: 3–7 дней, 15–20 минут в день. Начните с малого шага.', canonical, jsonLd, body });
}

async function fetchTable(table, qs) {
  const res = await fetch(`${SUPABASE_URL}/rest/v1/${table}?${qs}`, {
    headers: { apikey: ANON_KEY, Authorization: `Bearer ${ANON_KEY}` },
  });
  if (!res.ok) throw new Error(`${table}: HTTP ${res.status} ${await res.text()}`);
  return res.json();
}

async function main() {
  const [posts, themes] = await Promise.all([
    fetchTable('posts', 'select=*&order=published_at.desc'),
    fetchTable('mini_course_themes', 'status=eq.published&order=sort_order.asc'),
  ]);

  let n = 0;
  for (const p of posts) {
    if (!p.slug) continue;
    const dir = join('dist', 'blog', p.slug);
    mkdirSync(dir, { recursive: true });
    writeFileSync(join(dir, 'index.html'), renderPost(p));
    n++;
  }

  mkdirSync(join('dist', 'tonus-doma'), { recursive: true });
  writeFileSync(join('dist', 'tonus-doma', 'index.html'), renderMiniCourses(themes));

  console.log(`prerender: сгенерировано ${n} постов + /tonus-doma`);
}

main().catch((e) => {
  console.error('prerender error:', e);
  process.exit(1);
});

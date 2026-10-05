import { createClient } from '@supabase/supabase-js';
import supabase from '../lib/db-client.js';

const SITE_URL = 'https://alina-body.fitness';

// Отдельный клиент на anon-ключе для публичных read-only запросов.
// service-role ключ периодически падает с PGRST303 «JWT issued at future»
// из-за рассинхрона часов Vercel; anon-ключ этой проблемы не имеет.
const anonSupabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.VITE_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.VITE_SUPABASE_ANON_KEY
);

function html(title, message) {
  return `<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${title}</title>
</head>
<body style="font-family:system-ui,-apple-system,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;background:#FBF7F2;color:#3A312C;margin:0">
  <div style="text-align:center;padding:24px;max-width:420px">
    <h1 style="font-size:22px;margin:0 0 12px">${title}</h1>
    <p style="margin:0;color:#6B5E57;line-height:1.5">${message}</p>
  </div>
</body>
</html>`;
}

async function handleThreadsCallback(req, res) {
  const { code, error, error_description } = req.query;

  if (error) {
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    return res.status(400).send(html('Ошибка авторизации', error_description || error));
  }
  if (!code) {
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    return res.status(400).send(html('Ошибка авторизации', 'Не получен код авторизации.'));
  }

  try {
    const { error: insErr } = await supabase
      .from('oauth_temp_codes')
      .insert({ provider: 'threads', code: String(code) });
    if (insErr) throw insErr;

    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    return res.status(200).send(html('Готово', 'Авторизация получена, можно закрыть вкладку.'));
  } catch (e) {
    console.error('threads callback error:', e);
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    return res.status(500).send(html('Ошибка', 'Не удалось сохранить код авторизации.'));
  }
}

function buildLlms(themes, posts) {
  const themeLines = (themes || [])
    .map((t) => {
      const tripwire = `«${t.tripwire_title}» (${t.tripwire_days} дня, ${Number(t.tripwire_price) || 0} ₽)`;
      const course = `${t.course_title} (${t.course_days} дней, ${Number(t.course_price) || 0} ₽)`;
      return `- **${t.title}** — трипваер ${tripwire}; полная программа: ${course}. Подробнее: ${SITE_URL}/tonus-doma`;
    })
    .join('\n');

  const postLines = (posts || [])
    .slice(0, 10)
    .map((p) => `- [${p.title}](${SITE_URL}/blog/${p.slug})`)
    .join('\n');

  return `# Alina Body

> Онлайн-платформа домашнего фитнеса для девушек 18–28. Короткие мини-курсы (3–7 дней, 15–20 минут в день) для тонуса, осанки и лёгкой энергии — без жёстких ограничений. Тренер — Алина.

Коротко о платформе:

- Мини-курсы по зонам тела: сначала трипваер на 3 дня (знакомство), затем полная программа на 7 дней.
- Оплата онлайн через ЮKassa, доступ сразу после оплаты в личном кабинете.
- Видео доступны только онлайн, PDF можно скачать.
- Подход «мягкая сила»: осанка, дыхание, глубокий кор, суставы — без изнурения.

## Ключевые страницы

- [Главная](${SITE_URL}/)
- [Мини-курсы](${SITE_URL}/tonus-doma)
- [Блог](${SITE_URL}/blog)
- [Вход](${SITE_URL}/auth)

## Мини-курсы

${themeLines || '— скоро'}

## Последние статьи

${postLines || '— скоро'}

## Соцсети

- [Instagram](https://www.instagram.com/alina_body_fitness)
- [Threads](https://www.threads.com/@alina_body_fitness)
`;
}

function buildSitemap(posts) {
  const staticPages = ['/', '/tonus-doma', '/blog', '/auth', '/terms', '/privacy']
    .map((p) => `  <url><loc>${SITE_URL}${p}</loc></url>`)
    .join('\n');

  const postUrls = (posts || [])
    .map((p) => {
      const d = p.published_at ? String(p.published_at).slice(0, 10) : '';
      const lastmod = d ? `\n    <lastmod>${d}</lastmod>` : '';
      return `  <url>\n    <loc>${SITE_URL}/blog/${p.slug}</loc>${lastmod}\n  </url>`;
    })
    .join('\n');

  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${staticPages}
${postUrls}
</urlset>`;
}

async function handleLlms(req, res) {
  try {
    const [themesRes, postsRes] = await Promise.all([
      anonSupabase.from('mini_course_themes').select('*').eq('status', 'published').order('sort_order', { ascending: true }),
      anonSupabase.from('posts').select('title, slug, published_at').order('published_at', { ascending: false }).limit(10),
    ]);
    if (themesRes.error) throw themesRes.error;
    if (postsRes.error) throw postsRes.error;

    res.setHeader('Content-Type', 'text/plain; charset=utf-8');
    res.setHeader('Cache-Control', 's-maxage=300, stale-while-revalidate');
    return res.status(200).send(buildLlms(themesRes.data, postsRes.data));
  } catch (e) {
    console.error('llms error:', e);
    return res.status(500).send('Internal server error');
  }
}

async function handleSitemap(req, res) {
  try {
    const { data: posts, error } = await anonSupabase
      .from('posts')
      .select('slug, published_at')
      .order('published_at', { ascending: false });
    if (error) throw error;

    res.setHeader('Content-Type', 'application/xml; charset=utf-8');
    res.setHeader('Cache-Control', 's-maxage=300, stale-while-revalidate');
    return res.status(200).send(buildSitemap(posts));
  } catch (e) {
    console.error('sitemap error:', e);
    return res.status(500).send('Internal server error');
  }
}

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  if (req.method === 'OPTIONS') return res.status(204).end();

  // Threads OAuth callback (не трогает остальные маршруты)
  if (req.query.provider === 'threads' && req.query.action === 'callback') {
    return handleThreadsCallback(req, res);
  }

  // Динамические файлы для ИИ-агентов и поисковиков
  if (req.query.format === 'llms') {
    return handleLlms(req, res);
  }
  if (req.query.format === 'sitemap') {
    return handleSitemap(req, res);
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  return res.status(200).json([]);
}

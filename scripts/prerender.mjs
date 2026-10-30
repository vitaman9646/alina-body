// Генерация статического HTML для блога и мини-курсов (prerender).
// Запускается после vite build: создаёт dist/blog/{slug}/index.html и
// dist/tonus-doma/index.html — их видят поисковики без JS (Яндекс и др.).
import { writeFileSync, mkdirSync, readFileSync } from 'node:fs';
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
<nav><a href="${SITE_URL}/">Главная</a><a href="https://t.me/alinabodyfree">Telegram-канал</a><a href="${SITE_URL}/blog">Блог</a></nav>
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
<div class="cta">Хочешь больше пользы? <a href="https://t.me/alinabodyfree">Подписаться на Telegram →</a></div>
</article>`;
  return page({ title: `${p.title} — Alina Body`, description: p.excerpt || p.title, canonical, image: p.cover_image, type: 'article', jsonLd, body });
}

// Лид-магниты (зеркало src/data/leadMagnets.ts — держать в синхроне).
const MEDIA = 'https://tmzoyfhcajnukqotqspp.supabase.co/storage/v1/object/public/alina-media/lead-magnet';
const LEAD_MAGNETS = [
  { slug: 'tarelka', title: 'Гарвардская тарелка', description: 'Простой способ собрать сбалансированный приём пищи — без подсчёта калорий. 6 карточек-шпаргалок.', cards: [['Как собрать тарелку','tarelka-1.jpg'],['Половина — клетчатка','tarelka-2.jpg'],['Четверть — белки','tarelka-3.jpg'],['Четверть — углеводы','tarelka-4.jpg'],['Жиры — без сектора','tarelka-5.jpg'],['Правила перекуса','tarelka-6.jpg']] },
  { slug: 'dnevnik', title: 'Дневник питания', description: 'Как вести дневник, чтобы увидеть, что на самом деле мешает результату.', cards: [['Дневник питания — зачем','dnevnik-1.jpg'],['Как вести дневник','dnevnik-2.jpg'],['Базовая активность','dnevnik-3.jpg']] },
  { slug: 'psihologia', title: 'Психология похудения', description: 'Как перестать заедать стресс и отличать голод от эмоций.', cards: [['Голод или эмоции?','psihologia-1.jpg'],['3 шага против заедания','psihologia-2.jpg'],['Практики успокоения','psihologia-3.jpg']] },
  { slug: 'faq', title: 'FAQ похудения', description: 'Честные ответы на самые частые вопросы о похудении.', cards: [['Почему не худею','faq-1.jpg'],['Вода и разгрузочные дни','faq-2.jpg'],['Процедуры и заменители','faq-3.jpg'],['Если есть особенности','faq-4.jpg']] },
  { slug: 'menu', title: 'Меню на неделю', description: 'Готовый план питания на 7 дней — без сложных рецептов.', cards: [['День 1','menu-1.jpg'],['День 2','menu-2.jpg'],['День 3','menu-3.jpg'],['День 4','menu-4.jpg'],['День 5','menu-5.jpg'],['День 6','menu-6.jpg'],['День 7','menu-7.jpg']] },
  { slug: 'spisok', title: 'Список покупок', description: 'Что купить, чтобы дома всегда было из чего приготовить полезно.', cards: [['Что класть в корзину','spisok-1.jpg'],['Принцип радуги','spisok-2.jpg'],['Читаем этикетки','spisok-3.jpg'],['Белок и клетчатка','spisok-4.jpg']] },
  { slug: 'supp', title: 'Спортпит и БАДы', description: 'Что делают аминокислоты и как принимать их с умом.', cards: [['ГАМК — спокойствие и сон','supp-new-1.jpg'],['Аргинин — кровоток','supp-new-2.jpg'],['Лизин — коллаген','supp-new-3.jpg'],['Схема приёма','supp-new-4.jpg'],['Правила приёма БАД','supp-new-5.jpg']] },
  { slug: 'liver', title: 'Здоровье печени', description: 'Как поддержать печень питанием и привычками — без «чисток» и «детоксов».', cards: [['Питание','liver-new-1.jpg'],['Образ жизни','liver-new-2.jpg'],['Расторопша','liver-new-3.jpg'],['Артишок','liver-new-4.jpg']] },
  { slug: 'tazovoe-dno', title: 'Тазовое дно', description: 'Базовые движения для контроля мышц тазового дна — мягко и без стеснения.', cards: [['Два треугольника','tazodno-1-dva-treugolnika.jpg'],['Перекаты таза','tazodno-2-perekaty.jpg'],['Напряжение ↔ расслабление','tazodno-3-napryazhenie.jpg'],['Дыхание','tazodno-4-dyhanie.jpg']] },
  { slug: 'domashnie-trenirovki', title: 'Тренировки дома', description: '4 экспресс-комплекса на всё тело — без зала и инвентаря.', cards: [['4 экспресс-тренировки','domashnie-trenirovki-1.jpg'],['Верх тела + пресс','domashnie-trenirovki-2.jpg'],['Ягодицы — базовый','domashnie-trenirovki-3.jpg'],['Ягодицы — посложнее','domashnie-trenirovki-4.jpg'],['Спина + руки','domashnie-trenirovki-5.jpg'],['Как заниматься','domashnie-trenirovki-6.jpg']] },
  { slug: 'metabolic-protocol', title: 'Метаболический протокол', description: 'Домашний режим без жёстких диет: тарелка 80/20, тёплые напитки и 25 минут в день.', cards: [['Метаболическая тарелка 80/20','metabolic-protocol-1.jpg'],['Тёплые напитки','metabolic-protocol-2.jpg'],['Интервалы 25 минут','metabolic-protocol-3.jpg'],['15 минут тишины','metabolic-protocol-4.jpg'],['Пряности в рационе','metabolic-protocol-5.jpg'],['Распорядок дня','metabolic-protocol-6.jpg']] },
  { slug: 'domashniy-uhod', title: 'Домашний уход и витамины', description: 'Маски, скрабы и витаминные шоты из того, что уже есть на кухне.', cards: [['Витаминные шоты','domashniy-uhod-1.jpg'],['Волосы: блеск и густота','domashniy-uhod-2.jpg'],['Маски для лица','domashniy-uhod-3.jpg'],['Скраб и тоник','domashniy-uhod-4.jpg'],['Скраб и обёртывание','domashniy-uhod-5.jpg'],['Руки и ноги','domashniy-uhod-6.jpg']] },
  { slug: 'asimetriya', title: 'Йога: асимметричное выравнивание', description: 'Практика для ровной спины и осанки — 30–40 минут на коврике.', cards: [['Дыхание 4:4','asimetriya-1.jpg'],['Разминка спины','asimetriya-2.jpg'],['Скручивания','asimetriya-3.jpg'],['Наклоны и вытяжение','asimetriya-4.jpg'],['Балансы и планки','asimetriya-5.jpg'],['Заминка','asimetriya-6.jpg']] },
  { slug: 'pitanie-podskazki', title: 'Что и когда есть', description: 'ГИ, ИИ и три пищевых окна — как время приёма меняет результат.', cards: [['ГИ и ИИ: в чём разница','pitanie-podskazki-1.jpg'],['Три пищевых окна','pitanie-podskazki-2.jpg'],['Крахмалы: не враг, а с умом','pitanie-podskazki-3.jpg'],['Фрукты: когда и сколько','pitanie-podskazki-4.jpg'],['Ягоды — лучший выбор','pitanie-podskazki-5.jpg'],['Вечер: что можно и что нет','pitanie-podskazki-6.jpg'],['Как снизить ГИ блюда','pitanie-podskazki-7.jpg']] },
  { slug: 'pohudenie-bez-ukolov', title: 'Похудение без уколов', description: 'Естественный путь к весу, который не возвращается.', cards: [['Почему вес набирается','pohudenie-bez-ukolov-1.jpg'],['Белок — ключ к сытости','pohudenie-bez-ukolov-2.jpg'],['Сон — регулятор аппетита','pohudenie-bez-ukolov-3.jpg'],['Силовые — сохранить мышцы','pohudenie-bez-ukolov-4.jpg'],['Интервальное голодание 16:8','pohudenie-bez-ukolov-5.jpg']] },
];

function renderLead(m) {
  const canonical = `${SITE_URL}/lead/${m.slug}`;
  const cards = m.cards.map(([title, file]) =>
    `<figure class="card"><img src="${esc(MEDIA + '/' + file)}" alt="${esc(title)}" loading="lazy" style="width:100%;border-radius:10px"><figcaption style="margin-top:8px;color:#6B5E57;font-size:14px">${esc(title)}</figcaption></figure>`
  ).join('');
  const body = `<article><h1>${esc(m.title)}</h1><p class="meta">${esc(m.description)}</p>${cards}<div class="cta">Получи все материалы бесплатно: <a href="https://t.me/alinabodyfree">Забрать в Telegram →</a></div></article>`;
  return page({ title: `${m.title} — бесплатная шпаргалка | Alina Body`, description: m.description, canonical, image: MEDIA + '/' + m.cards[0][1], type: 'website', jsonLd: [], body });
}

function renderRecipe(r) {
  const canonical = `${SITE_URL}/recipe/${r.slug}`;
  const jsonLd = [{
    '@context': 'https://schema.org', '@type': 'Recipe',
    name: r.name,
    description: `Простой ПП-рецепт: ${r.name}.`,
    image: [r.image],
    recipeIngredient: [r.ingredients],
    recipeInstructions: [{ '@type': 'HowToStep', text: r.method }],
  }];
  const body = `<article><h1>${esc(r.name)}</h1>${r.category ? `<div class=\"meta\">${esc(r.category)}</div>` : ''}<img class=\"cover\" src=\"${esc(r.image)}\" alt=\"${esc(r.name)}\"><h2>Ингредиенты</h2><div class=\"content\"><p>${esc(r.ingredients)}</p><h2>Приготовление</h2><p>${esc(r.method)}</p></div><div class=\"cta\">Больше рецептов: <a href=\"https://t.me/alinabodyfree\">Telegram-канал Алины →</a></div></article>`;
  return page({ title: `${r.name} — рецепт | Alina Body`, description: `${r.name}: ингредиенты и приготовление. Простой ПП-рецепт.`, canonical, image: r.image, type: 'website', jsonLd, body });
}

async function fetchTable(table, qs) {
  const res = await fetch(`${SUPABASE_URL}/rest/v1/${table}?${qs}`, {
    headers: { apikey: ANON_KEY, Authorization: `Bearer ${ANON_KEY}` },
  });
  if (!res.ok) throw new Error(`${table}: HTTP ${res.status} ${await res.text()}`);
  return res.json();
}

async function main() {
  const posts = await fetchTable('posts', 'select=*&order=published_at.desc');

  let n = 0;
  for (const p of posts) {
    if (!p.slug) continue;
    const dir = join('dist', 'blog', p.slug);
    mkdirSync(dir, { recursive: true });
    writeFileSync(join(dir, 'index.html'), renderPost(p));
    n++;
  }

  console.log(`prerender: сгенерировано ${n} постов`);

  let m = 0;
  for (const lm of LEAD_MAGNETS) {
    const dir = join('dist', 'lead', lm.slug);
    mkdirSync(dir, { recursive: true });
    writeFileSync(join(dir, 'index.html'), renderLead(lm));
    m++;
  }
  console.log(`prerender: сгенерировано ${m} лид-магнитов`);

  try {
    const recipes = JSON.parse(readFileSync('public/recipes.json', 'utf8'));
    for (const r of recipes) {
      const dir = join('dist', 'recipe', r.slug);
      mkdirSync(dir, { recursive: true });
      writeFileSync(join(dir, 'index.html'), renderRecipe(r));
    }
    console.log(`prerender: сгенерировано ${recipes.length} рецептов`);
  } catch (e) {
    console.log('prerender: recipes.json нет — пропускаю рецепты');
  }
}

main().catch((e) => {
  console.error('prerender error:', e);
  process.exit(1);
});

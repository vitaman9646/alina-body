import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.VITE_SUPABASE_URL,
  process.env.VITE_SUPABASE_ANON_KEY
);

const SITE_URL = 'https://alina-body.com';

export default async function handler(req, res) {
  try {
    const { data: posts, error } = await supabase
      .from('posts')
      .select('*')
      .order('published_at', { ascending: false })
      .limit(20);

    if (error) throw error;

    const items = (posts || []).map(post => {
      const articleUrl = `${SITE_URL}/blog/${post.slug}?utm_source=dzen&utm_medium=rss&utm_campaign=${post.slug}`;
      const coverUrl = post.cover_image || `${SITE_URL}/default-cover.jpg`;
      
      return `
    <item>
      <title><![CDATA[${post.title}]]></title>
      <link>${articleUrl}</link>
      <guid isPermaLink="true">${articleUrl}</guid>
      <pubDate>${new Date(post.published_at).toUTCString()}</pubDate>
      <content:encoded><![CDATA[${post.content}]]></content:encoded>
      <media:content url="${coverUrl}" medium="image">
        <media:title type="plain">${post.title}</media:title>
      </media:content>
      <category>format-article</category>
    </item>`;
    }).join('');

    const rss = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <title>Alina Body — Фитнес, питание, привычки</title>
    <link>${SITE_URL}</link>
    <description>Практические советы по фитнесу, тренировкам и здоровому образу жизни от ИИ-модели Алины</description>
    <language>ru</language>
    <lastBuildDate>${new Date().toUTCString()}</lastBuildDate>
    <atom:link href="${SITE_URL}/api/rss" rel="self" type="application/rss+xml" xmlns:atom="http://www.w3.org/2005/Atom"/>
    ${items}
  </channel>
</rss>`;

    res.setHeader('Content-Type', 'application/rss+xml; charset=utf-8');
    res.setHeader('Cache-Control', 's-maxage=300, stale-while-revalidate');
    return res.status(200).send(rss);
  } catch (error) {
    console.error('RSS error:', error);
    return res.status(500).send('Error generating RSS');
  }
}

export const config = {
  runtime: 'nodejs',
};

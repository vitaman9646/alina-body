import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.VITE_SUPABASE_URL,
  process.env.VITE_SUPABASE_ANON_KEY
);

export default async function handler(req, res) {
  const { slug } = req.query;

  try {
    if (slug) {
      const { data, error } = await supabase
        .from('posts')
        .select('*')
        .eq('slug', slug)
        .single();

      if (error || !data) {
        return res.status(404).json({ error: 'Article not found' });
      }

      return res.status(200).json(data);
    }

    const { data, error } = await supabase
      .from('posts')
      .select('id, title, slug, excerpt, cover_image, published_at')
      .order('published_at', { ascending: false });

    if (error) throw error;

    res.setHeader('Cache-Control', 's-maxage=300, stale-while-revalidate');
    return res.status(200).json(data || []);
  } catch (error) {
    console.error('Posts API error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}

export const config = {
  runtime: 'nodejs',
};

import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.VITE_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.VITE_SUPABASE_ANON_KEY
);

function mapCourse(c) {
  const isChallenge =
    (c.slug && String(c.slug).includes('challenge')) ||
    (c.level && String(c.level).includes('challenge'));

  return {
    id: c.id,
    slug: c.slug,
    title: c.title,
    short_title: c.short_description || c.title,
    type: isChallenge ? 'challenge' : 'course',
    tagline: c.short_description || '',
    description: c.description || c.short_description || '',
    duration_label: c.duration_days ? `${c.duration_days} дней` : '',
    price: Number(c.price) || 0,
    next_start: '',
    seats_note: c.is_free ? 'Бесплатный тест' : '',
    image_url: c.cover_url || '',
    video_count: 0,
    session_minutes: '',
    highlights: c.short_description ? [c.short_description] : [],
    is_featured: true,
    sort_order: c.sort_order ?? 0,
    tariffs: [
      {
        id: 1,
        program_id: c.id,
        slug: 'default',
        name: c.is_free ? 'Бесплатно' : 'Стандарт',
        price: Number(c.price) || 0,
        access_days: c.duration_days || 30,
        description: c.short_description || '',
        features: [],
        is_popular: true,
        sort_order: 1,
      },
    ],
  };
}

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const slug = req.query.slug;

    if (slug) {
      const { data: course, error } = await supabase
        .from('courses')
        .select('*')
        .eq('slug', slug)
        .single();
      if (error) throw error;
      if (!course) return res.status(404).json({ error: 'Курс не найден' });
      return res.status(200).json(mapCourse(course));
    }

    const { data, error } = await supabase
      .from('courses')
      .select('*')
      .eq('status', 'published')
      .order('sort_order', { ascending: true });
    if (error) throw error;
    return res.status(200).json((data || []).map(mapCourse));
  } catch (err) {
    console.error('programs error:', err);
    return res.status(500).json({ error: err.message || String(err) });
  }
}

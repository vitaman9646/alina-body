import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.VITE_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.VITE_SUPABASE_ANON_KEY
);

function mapTheme(t) {
  return {
    id: t.id,
    slug: t.slug,
    title: t.title,
    voiceLine: t.voice_line,
    tripwire: {
      title: t.tripwire_title,
      days: t.tripwire_days,
      minutesPerDay: t.tripwire_minutes_per_day,
      price: Number(t.tripwire_price) || 0,
      slug: t.tripwire_slug,
      image: t.tripwire_image_url || '',
    },
    course: {
      title: t.course_title,
      days: t.course_days,
      price: Number(t.course_price) || 0,
      slug: t.course_slug,
      image: t.course_image_url || '',
    },
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
    const { data, error } = await supabase
      .from('mini_course_themes')
      .select('*')
      .eq('status', 'published')
      .order('sort_order', { ascending: true });
    if (error) throw error;
    return res.status(200).json((data || []).map(mapTheme));
  } catch (err) {
    console.error('mini-course-themes error:', err);
    return res.status(500).json({ error: err.message || String(err) });
  }
}

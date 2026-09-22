import { createClient } from '@supabase/supabase-js';
import { mapCourse } from '../lib/mappers.js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.VITE_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.VITE_SUPABASE_ANON_KEY
);

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

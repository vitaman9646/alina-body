import { createClient } from '@supabase/supabase-js';

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

      const { data: modules, error: mErr } = await supabase
        .from('course_modules')
        .select('*')
        .eq('course_id', course.id)
        .order('sort_order', { ascending: true });
      if (mErr) throw mErr;

      const moduleIds = (modules || []).map((m) => m.id);
      let lessons = [];
      if (moduleIds.length) {
        const { data: lessonsData, error: lErr } = await supabase
          .from('course_lessons')
          .select(
            'id, module_id, title, description, lesson_type, duration_minutes, is_preview, sort_order'
          )
          .in('module_id', moduleIds)
          .order('sort_order', { ascending: true });
        if (lErr) throw lErr;
        lessons = lessonsData || [];
      }

      return res.status(200).json({
        ...course,
        modules: (modules || []).map((m) => ({
          ...m,
          lessons: lessons.filter((l) => l.module_id === m.id),
        })),
      });
    }

    const { data, error } = await supabase
      .from('courses')
      .select(
        'id, slug, title, short_description, price, currency, duration_days, level, status, is_free, sort_order, cover_url'
      )
      .eq('status', 'published')
      .order('sort_order', { ascending: true });

    if (error) throw error;
    return res.status(200).json(data || []);
  } catch (err) {
    console.error('programs/courses error:', err);
    return res.status(500).json({ error: err.message || String(err) });
  }
}

import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.VITE_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.VITE_SUPABASE_ANON_KEY
);

// Для публичной витрины курса: читаем ВСЕ уроки (метаданные) в обход RLS,
// возвращаем только публичные поля (title/description/photo), без content и video.
const supabaseAdmin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.VITE_SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
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

  const { slug } = req.query;

  try {
    // Детальная страница курса (публичная витрина: что внутри, описания упражнений)
    if (slug) {
      const { data: course, error: cErr } = await supabaseAdmin
        .from('courses')
        .select('*')
        .eq('slug', slug)
        .single();
      if (cErr || !course) {
        return res.status(404).json({ error: 'Курс не найден' });
      }

      const { data: modules } = await supabaseAdmin
        .from('course_modules')
        .select('*')
        .eq('course_id', course.id)
        .order('sort_order', { ascending: true });

      const moduleIds = (modules || []).map((m) => m.id);
      let lessons = [];
      if (moduleIds.length) {
        const { data } = await supabaseAdmin
          .from('course_lessons')
          .select('*')
          .in('module_id', moduleIds)
          .order('sort_order', { ascending: true });
        lessons = data || [];
      }

      const byModule = {};
      for (const l of lessons) {
        (byModule[l.module_id] = byModule[l.module_id] || []).push({
          title: l.title,
          description: l.description || '',
          image: l.file_url || null,
          duration_min: l.duration_minutes || null,
        });
      }

      return res.status(200).json({
        slug: course.slug,
        title: course.title,
        description: course.description || '',
        price: Number(course.price) || 0,
        currency: course.currency || 'RUB',
        duration_days: course.duration_days || 7,
        level: course.level || '',
        cover_url: course.cover_url || null,
        modules: (modules || []).map((m) => ({
          title: m.title,
          description: m.description || '',
          lessons: byModule[m.id] || [],
        })),
      });
    }

    // Список тем (витрина мини-курсов)
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

import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.VITE_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || process.env.VITE_SUPABASE_ANON_KEY
);

// Публичная витрина: читаем метаданные в обход RLS (счётчики модулей/уроков),
// возвращаем только публичные поля — без content и video.
const supabaseAdmin = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.VITE_SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
);

// Категории — статичный упорядоченный список (как reviews/FAQ). Курс привязывается к
// категории полем `courses.category` (slug). Добавить категорию = добавить запись сюда.
const CATEGORIES = [
  { slug: 'pitanie', title: 'Питание', description: 'Рецепты с граммовками и КБЖУ, техники готовки, бюджетное меню' },
];

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { slug } = req.query;

  try {
    // Детальная страница курса (публичная витрина: что внутри, описания уроков)
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
        id: course.id,
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

    // Список категорий → курсы (вкладка «Мини-курсы»)
    const { data: courses, error: cErr2 } = await supabaseAdmin
      .from('courses')
      .select('id, slug, title, short_description, cover_url, price, currency, duration_days, level, category')
      .not('category', 'is', null)
      .order('sort_order', { ascending: true });

    if (cErr2) throw cErr2;

    const courseIds = (courses || []).map((c) => c.id);
    let moduleRows = [];
    let lessonRows = [];
    if (courseIds.length) {
      const { data: mods } = await supabaseAdmin
        .from('course_modules')
        .select('id, course_id')
        .in('course_id', courseIds);
      moduleRows = mods || [];
      const modIds = moduleRows.map((m) => m.id);
      if (modIds.length) {
        const { data: less } = await supabaseAdmin
          .from('course_lessons')
          .select('id, module_id')
          .in('module_id', modIds);
        lessonRows = less || [];
      }
    }

    const lessonsByModule = {};
    for (const l of lessonRows) {
      lessonsByModule[l.module_id] = (lessonsByModule[l.module_id] || 0) + 1;
    }
    const modulesByCourse = {};
    for (const m of moduleRows) {
      modulesByCourse[m.course_id] = (modulesByCourse[m.course_id] || 0) + 1;
    }
    const lessonsByCourse = {};
    for (const m of moduleRows) {
      lessonsByCourse[m.course_id] = (lessonsByCourse[m.course_id] || 0) + (lessonsByModule[m.id] || 0);
    }

    const byCat = {};
    for (const c of courses) {
      (byCat[c.category] = byCat[c.category] || []).push({
        id: c.id,
        slug: c.slug,
        title: c.title,
        short_description: c.short_description || '',
        cover_url: c.cover_url || null,
        price: Number(c.price) || 0,
        currency: c.currency || 'RUB',
        duration_days: c.duration_days || 0,
        level: c.level || '',
        modules_count: modulesByCourse[c.id] || 0,
        lessons_count: lessonsByCourse[c.id] || 0,
      });
    }

    const categories = CATEGORIES.filter((cat) => byCat[cat.slug]?.length).map((cat) => ({
      slug: cat.slug,
      title: cat.title,
      description: cat.description,
      courses: byCat[cat.slug],
    }));

    return res.status(200).json({ categories });
  } catch (err) {
    console.error('mini-course-themes error:', err);
    return res.status(500).json({ error: err.message || String(err) });
  }
}

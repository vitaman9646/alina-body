import supabase from '../lib/db-client.js';
import { setCors, getUserFromReq } from '../lib/utils.js';

// Просмотрщик курса (закрытая часть после оплаты).
// Возвращает структуру курса (модули → уроки) с телом уроков (content/video)
// ТОЛЬКО при оплаченном доступе (course_purchases.status='paid').
// Названия и описания уроков публичны (показываются и на лендинге),
// но контент (рецепт/техника) и видео отдаются лишь покупателю.
export default async function handler(req, res) {
  setCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

  try {
    const { slug } = req.query;
    if (!slug) return res.status(400).json({ error: 'Не указан курс' });

    const user = await getUserFromReq(req);
    if (!user) return res.status(401).json({ error: 'Нужна авторизация' });

    const { data: course, error: cErr } = await supabase
      .from('courses')
      .select('*')
      .eq('slug', slug)
      .single();
    if (cErr || !course) return res.status(404).json({ error: 'Курс не найден' });

    const { data: paid } = await supabase
      .from('course_purchases')
      .select('id')
      .eq('user_id', user.id)
      .eq('course_id', course.id)
      .eq('status', 'paid')
      .limit(1);
    const hasAccess = !!(paid && paid.length);

    const { data: modules } = await supabase
      .from('course_modules')
      .select('*')
      .eq('course_id', course.id)
      .order('sort_order', { ascending: true });

    const moduleIds = (modules || []).map((m) => m.id);
    let lessons = [];
    if (moduleIds.length) {
      const { data } = await supabase
        .from('course_lessons')
        .select('*')
        .in('module_id', moduleIds)
        .order('sort_order', { ascending: true });
      lessons = data || [];
    }

    const { data: progress } = await supabase
      .from('lesson_progress')
      .select('lesson_id, is_completed')
      .eq('user_id', user.id);

    const byModule = {};
    for (const m of modules || []) {
      byModule[m.id] = { id: m.id, title: m.title, description: m.description || '', lessons: [] };
    }
    for (const l of lessons) {
      const slot = byModule[l.module_id];
      if (!slot) continue;
      slot.lessons.push({
        id: l.id,
        title: l.title,
        description: l.description || '',
        lesson_type: l.lesson_type || 'text',
        duration_minutes: l.duration_minutes || null,
        is_preview: !!l.is_preview,
        locked: !hasAccess,
        file_url: l.file_url || null, // фото публично (то же самое на лендинге)
        video_url: hasAccess ? l.video_url : null,
        content: hasAccess ? l.content : null, // тело — только покупателю
        sort_order: l.sort_order ?? 0,
      });
    }

    const done = {};
    for (const p of progress || []) {
      if (p.is_completed) done[p.lesson_id] = true;
    }

    return res.status(200).json({
      course: {
        id: course.id,
        slug: course.slug,
        title: course.title,
        description: course.description || '',
        cover_url: course.cover_url || null,
        price: Number(course.price) || 0,
        currency: course.currency || 'RUB',
      },
      access: hasAccess ? 'paid' : 'none',
      modules: Object.values(byModule),
      progress: done,
    });
  } catch (err) {
    console.error('course-viewer error:', err);
    return res.status(500).json({ error: err.message || String(err) });
  }
}

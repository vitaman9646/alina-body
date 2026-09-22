import supabase from '../lib/db-client.js';
import { setCors, getUserFromReq, findEnrollment } from '../lib/utils.js';

function mapLesson(l, courseId) {
  return {
    id: l.id,
    program_id: courseId,
    week: null,
    day: l.sort_order ?? null,
    title: l.title,
    duration_min: l.duration_minutes ?? null,
    description: l.description,
    video_url: l.video_url,
    is_preview: l.is_preview,
    locked: !l.is_preview,
    sort_order: l.sort_order ?? 0,
  };
}

function hideVideo(lesson) {
  return { ...lesson, video_url: lesson.is_preview ? lesson.video_url : null, locked: !lesson.is_preview };
}

async function courseIdForModule(moduleId) {
  const { data: mod } = await supabase
    .from('course_modules')
    .select('course_id')
    .eq('id', moduleId)
    .single();
  return mod?.course_id ?? null;
}

export default async function handler(req, res) {
  setCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();
  try {
    if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

    const { program_id, slug, id } = req.query;
    const user = await getUserFromReq(req);

    if (id) {
      const { data: lesson, error: lErr } = await supabase
        .from('course_lessons')
        .select('*')
        .eq('id', id)
        .single();
      if (lErr) throw lErr;
      if (!lesson) return res.status(404).json({ error: 'Урок не найден' });

      const courseId = await courseIdForModule(lesson.module_id);
      const mapped = mapLesson(lesson, courseId);

      let allowed = !!lesson.is_preview;
      if (user && courseId) {
        allowed = allowed || !!(await findEnrollment(user.id, courseId));
      }
      if (!allowed) {
        return res.status(200).json({ ...hideVideo(mapped), locked: true });
      }
      return res.status(200).json({ ...mapped, locked: false });
    }

    let courseId = program_id ? String(program_id) : null;
    if (!courseId && slug) {
      const { data: course } = await supabase.from('courses').select('id').eq('slug', slug).single();
      courseId = course?.id ?? null;
    }

    let lessons = [];
    if (courseId) {
      const { data: mods } = await supabase
        .from('course_modules')
        .select('id')
        .eq('course_id', courseId);
      const moduleIds = (mods || []).map((m) => m.id);
      if (moduleIds.length) {
        const { data } = await supabase
          .from('course_lessons')
          .select('*')
          .in('module_id', moduleIds)
          .order('sort_order', { ascending: true });
        lessons = data || [];
      }
    } else {
      const { data } = await supabase
        .from('course_lessons')
        .select('*')
        .order('sort_order', { ascending: true });
      lessons = data || [];
    }

    const moduleIds = [...new Set(lessons.map((l) => l.module_id))];
    const moduleToCourse = {};
    if (moduleIds.length) {
      const { data: mods } = await supabase
        .from('course_modules')
        .select('id, course_id')
        .in('id', moduleIds);
      for (const m of (mods || [])) moduleToCourse[m.id] = m.course_id;
    }

    let enrolledCourseIds = new Set();
    if (user) {
      const { data: purchases } = await supabase
        .from('course_purchases')
        .select('course_id')
        .eq('user_id', user.id);
      enrolledCourseIds = new Set((purchases || []).map((p) => p.course_id));
    }

    const mapped = lessons.map((lesson) => {
      const cid = moduleToCourse[lesson.module_id];
      const allowed = lesson.is_preview || enrolledCourseIds.has(cid);
      const base = mapLesson(lesson, cid);
      return allowed ? { ...base, locked: false } : hideVideo(base);
    });

    return res.status(200).json(mapped);
  } catch (err) {
    console.error('lessons error:', err);
    res.status(500).json({ error: err.message });
  }
}

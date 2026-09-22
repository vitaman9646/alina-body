import supabase from '../lib/db-client.js';
import { setCors, getUserFromReq, findEnrollment } from '../lib/utils.js';

function toRow(r) {
  return {
    id: r.id,
    user_id: r.user_id,
    lesson_id: r.lesson_id,
    completed: r.is_completed,
    completed_at: r.completed_at,
  };
}

async function resolveCourseId(lessonId) {
  const { data: lesson } = await supabase
    .from('course_lessons')
    .select('module_id')
    .eq('id', lessonId)
    .single();
  if (!lesson?.module_id) return null;
  const { data: mod } = await supabase
    .from('course_modules')
    .select('course_id')
    .eq('id', lesson.module_id)
    .single();
  return mod?.course_id ?? null;
}

export default async function handler(req, res) {
  setCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();
  try {
    const user = await getUserFromReq(req);
    if (!user) return res.status(401).json({ error: 'Нужна авторизация' });

    if (req.method === 'GET') {
      const { data, error } = await supabase
        .from('lesson_progress')
        .select('*')
        .eq('user_id', user.id)
        .order('id', { ascending: true });
      if (error) throw error;
      return res.status(200).json((data || []).map(toRow));
    }

    if (req.method === 'POST' || req.method === 'PUT') {
      const { lesson_id, completed } = req.body || {};
      if (!lesson_id) return res.status(400).json({ error: 'Не указан урок' });

      const courseId = await resolveCourseId(lesson_id);
      if (!courseId) return res.status(404).json({ error: 'Урок не найден' });

      const enrollment = await findEnrollment(user.id, courseId);
      if (!enrollment) return res.status(403).json({ error: 'Нет доступа к программе' });

      const done = completed !== false;
      const now = done ? new Date().toISOString() : null;
      const ts = new Date().toISOString();

      const { data: existing } = await supabase
        .from('lesson_progress')
        .select('*')
        .eq('user_id', user.id)
        .eq('lesson_id', lesson_id)
        .limit(1);

      if (existing?.[0]) {
        const { data, error } = await supabase
          .from('lesson_progress')
          .update({ is_completed: done, completed_at: now, updated_at: ts })
          .eq('id', existing[0].id)
          .select()
          .single();
        if (error) throw error;
        return res.status(200).json(toRow(data));
      }

      const { data, error } = await supabase
        .from('lesson_progress')
        .insert({
          user_id: user.id,
          lesson_id,
          is_completed: done,
          completed_at: now,
          updated_at: ts,
        })
        .select()
        .single();
      if (error) throw error;
      return res.status(201).json(toRow(data));
    }

    res.status(405).json({ error: 'Method not allowed' });
  } catch (err) {
    console.error('progress error:', err);
    res.status(500).json({ error: err.message });
  }
}

import supabase from '../lib/db-client.js';
import { setCors, getUserFromReq, findEnrollment } from '../lib/utils.js';

export default async function handler(req, res) {
  setCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();

  try {
    const user = await getUserFromReq(req);
    if (!user) return res.status(401).json({ error: 'Нужна авторизация' });

    if (req.method === 'GET') {
      const { data, error } = await supabase
        .from('progress')
        .select('*')
        .eq('user_id', user.id)
        .order('id', { ascending: true });
      if (error) throw error;
      return res.status(200).json(data || []);
    }

    if (req.method === 'POST' || req.method === 'PUT') {
      const { lesson_id, completed } = req.body || {};
      if (!lesson_id) return res.status(400).json({ error: 'Не указан урок' });

      const { data: lesson, error: lErr } = await supabase
        .from('lessons')
        .select('*')
        .eq('id', lesson_id)
        .single();
      if (lErr) throw lErr;
      if (!lesson) return res.status(404).json({ error: 'Урок не найден' });

      const enrollment = await findEnrollment(user.id, lesson.program_id);
      if (!enrollment) return res.status(403).json({ error: 'Нет доступа к программе' });

      const { data: existing } = await supabase
        .from('progress')
        .select('*')
        .eq('user_id', user.id)
        .eq('lesson_id', lesson_id)
        .limit(1);

      const done = completed !== false;
      if (existing?.[0]) {
        const { data, error } = await supabase
          .from('progress')
          .update({
            completed: done,
            completed_at: done ? new Date().toISOString() : null,
          })
          .eq('id', existing[0].id)
          .select()
          .single();
        if (error) throw error;
        return res.status(200).json(data);
      }

      const { data, error } = await supabase
        .from('progress')
        .insert({
          user_id: user.id,
          lesson_id,
          completed: done,
          completed_at: done ? new Date().toISOString() : null,
        })
        .select()
        .single();
      if (error) throw error;
      return res.status(201).json(data);
    }

    res.status(405).json({ error: 'Method not allowed' });
  } catch (err) {
    console.error('progress error:', err);
    res.status(500).json({ error: err.message });
  }
}

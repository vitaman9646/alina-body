import supabase from '../lib/db-client.js';
import { setCors, getUserFromReq } from '../lib/utils.js';

function extOf(url) {
  if (!url) return '';
  const clean = String(url).split('?')[0];
  const m = clean.match(/\.([a-zA-Z0-9]+)$/);
  return m ? m[1].toLowerCase() : '';
}

export default async function handler(req, res) {
  setCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();
  try {
    if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

    const programId = req.query.program_id ? String(req.query.program_id) : null;
    const user = await getUserFromReq(req);

    let lessons = [];
    if (programId) {
      const { data: mods } = await supabase.from('course_modules').select('id').eq('course_id', programId);
      const moduleIds = (mods || []).map((m) => m.id);
      if (moduleIds.length) {
        const { data } = await supabase
          .from('course_lessons')
          .select('*')
          .in('module_id', moduleIds)
          .not('file_url', 'is', null)
          .order('sort_order', { ascending: true });
        lessons = data || [];
      }
    } else {
      const { data } = await supabase
        .from('course_lessons')
        .select('*')
        .not('file_url', 'is', null)
        .order('sort_order', { ascending: true });
      lessons = data || [];
    }

    const moduleIds = [...new Set(lessons.map((l) => l.module_id))];
    const moduleToCourse = {};
    if (moduleIds.length) {
      const { data: mods } = await supabase.from('course_modules').select('id, course_id').in('id', moduleIds);
      for (const m of (mods || [])) moduleToCourse[m.id] = m.course_id;
    }

    let enrolled = new Set();
    if (user) {
      const { data: purchases } = await supabase.from('course_purchases').select('course_id').eq('user_id', user.id);
      enrolled = new Set((purchases || []).map((p) => p.course_id));
    }

    const mapped = lessons.map((l) => {
      const cid = moduleToCourse[l.module_id];
      const allowed = enrolled.has(cid);
      return {
        id: l.id,
        program_id: cid,
        title: l.title,
        description: l.description,
        file_url: allowed ? l.file_url : null,
        file_type: l.lesson_type || extOf(l.file_url) || 'pdf',
        locked: !allowed,
      };
    });

    return res.status(200).json(mapped);
  } catch (err) {
    console.error('materials error:', err);
    res.status(500).json({ error: err.message });
  }
}

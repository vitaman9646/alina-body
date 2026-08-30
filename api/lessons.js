import supabase from '../lib/db-client.js';
import { setCors, getUserFromReq, findEnrollment } from '../lib/utils.js';

function hideVideo(lesson) {
  const { video_url, ...rest } = lesson;
  return { ...rest, video_url: lesson.is_preview ? video_url : null, locked: !lesson.is_preview };
}

export default async function handler(req, res) {
  setCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();

  try {
    if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

    const { program_id, slug, id } = req.query;
    const user = await getUserFromReq(req);

    if (id) {
      const { data: lesson, error } = await supabase.from('lessons').select('*').eq('id', id).single();
      if (error) throw error;
      if (!lesson) return res.status(404).json({ error: 'Урок не найден' });

      let allowed = !!lesson.is_preview;
      if (user) {
        const enrollment = await findEnrollment(user.id, lesson.program_id);
        allowed = allowed || !!enrollment;
      }
      if (!allowed) {
        return res.status(200).json({ ...hideVideo(lesson), locked: true });
      }
      return res.status(200).json({ ...lesson, locked: false });
    }

    let programId = program_id ? Number(program_id) : null;
    if (!programId && slug) {
      const { data: program, error: pErr } = await supabase
        .from('programs')
        .select('id')
        .eq('slug', slug)
        .single();
      if (pErr) throw pErr;
      programId = program?.id;
    }

    let query = supabase.from('lessons').select('*').order('sort_order', { ascending: true });
    if (programId) query = query.eq('program_id', programId);

    const { data, error } = await query;
    if (error) throw error;

    let enrolledProgramIds = new Set();
    if (user) {
      const { data: ens } = await supabase.from('enrollments').select('program_id').eq('user_id', user.id);
      enrolledProgramIds = new Set((ens || []).map((e) => e.program_id));
    }

    const mapped = (data || []).map((lesson) => {
      const allowed = lesson.is_preview || enrolledProgramIds.has(lesson.program_id);
      return allowed ? { ...lesson, locked: false } : hideVideo(lesson);
    });

    return res.status(200).json(mapped);
  } catch (err) {
    console.error('lessons error:', err);
    res.status(500).json({ error: err.message });
  }
}

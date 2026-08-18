import supabase from './db-client.js';
import { setCors, getUserFromReq } from './utils.js';

export default async function handler(req, res) {
  setCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();

  try {
    if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

    const programId = req.query.program_id ? Number(req.query.program_id) : null;
    let query = supabase.from('materials').select('*').order('id', { ascending: true });
    if (programId) query = query.eq('program_id', programId);
    const { data, error } = await query;
    if (error) throw error;

    const user = await getUserFromReq(req);
    let enrolled = new Set();
    if (user) {
      const { data: ens } = await supabase.from('enrollments').select('program_id').eq('user_id', user.id);
      enrolled = new Set((ens || []).map((e) => e.program_id));
    }

    const mapped = (data || []).map((m) => {
      const allowed = enrolled.has(m.program_id);
      return {
        ...m,
        file_url: allowed ? m.file_url : null,
        locked: !allowed,
      };
    });

    return res.status(200).json(mapped);
  } catch (err) {
    console.error('materials error:', err);
    res.status(500).json({ error: err.message });
  }
}

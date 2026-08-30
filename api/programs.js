import supabase from '../lib/db-client.js';
import { setCors, parseJsonField } from '../lib/utils.js';

export default async function handler(req, res) {
  setCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();

  try {
    if (req.method !== 'GET') {
      return res.status(405).json({ error: 'Method not allowed' });
    }

    const slug = req.query.slug;
    let query = supabase.from('programs').select('*').order('sort_order', { ascending: true });
    if (slug) query = query.eq('slug', slug);

    const { data: programs, error } = await query;
    if (error) throw error;

    const { data: tariffs, error: tErr } = await supabase
      .from('tariffs')
      .select('*')
      .order('sort_order', { ascending: true });
    if (tErr) throw tErr;

    const mapped = (programs || []).map((p) => ({
      ...p,
      highlights: parseJsonField(p.highlights),
      tariffs: (tariffs || [])
        .filter((t) => t.program_id === p.id)
        .map((t) => ({ ...t, features: parseJsonField(t.features) })),
    }));

    if (slug) {
      if (!mapped.length) return res.status(404).json({ error: 'Программа не найдена' });
      return res.status(200).json(mapped[0]);
    }

    return res.status(200).json(mapped);
  } catch (err) {
    console.error('programs error:', err);
    res.status(500).json({ error: err.message });
  }
}

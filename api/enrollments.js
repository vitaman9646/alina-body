import supabase from './db-client.js';
import { setCors, getUserFromReq, parseJsonField } from './utils.js';

export default async function handler(req, res) {
  setCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();

  try {
    if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

    const user = await getUserFromReq(req);
    if (!user) return res.status(401).json({ error: 'Нужна авторизация' });

    const { data: enrollments, error } = await supabase
      .from('enrollments')
      .select('*')
      .eq('user_id', user.id)
      .order('id', { ascending: false });
    if (error) throw error;

    const programIds = [...new Set((enrollments || []).map((e) => e.program_id))];
    let programs = [];
    let tariffs = [];
    if (programIds.length) {
      const { data: p } = await supabase.from('programs').select('*').in('id', programIds);
      const { data: t } = await supabase.from('tariffs').select('*');
      programs = p || [];
      tariffs = t || [];
    }

    const mapped = (enrollments || []).map((e) => {
      const program = programs.find((p) => p.id === e.program_id);
      const tariff = tariffs.find((t) => t.id === e.tariff_id);
      return {
        ...e,
        program: program
          ? { ...program, highlights: parseJsonField(program.highlights) }
          : null,
        tariff: tariff ? { ...tariff, features: parseJsonField(tariff.features) } : null,
      };
    });

    return res.status(200).json(mapped);
  } catch (err) {
    console.error('enrollments error:', err);
    res.status(500).json({ error: err.message });
  }
}

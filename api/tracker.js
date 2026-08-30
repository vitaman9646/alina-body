import supabase from '../lib/db-client.js';
import { setCors, getUserFromReq, findEnrollment } from '../lib/utils.js';

export default async function handler(req, res) {
  setCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();

  try {
    const user = await getUserFromReq(req);
    if (!user) return res.status(401).json({ error: 'Нужна авторизация' });

    if (req.method === 'GET') {
      const programId = req.query.program_id;
      let query = supabase.from('tracker').select('*').eq('user_id', user.id).order('day_number', { ascending: true });
      if (programId) query = query.eq('program_id', Number(programId));
      const { data, error } = await query;
      if (error) throw error;
      return res.status(200).json(data || []);
    }

    if (req.method === 'POST' || req.method === 'PUT') {
      const { program_id, day_number, mood, energy, note } = req.body || {};
      if (!program_id || !day_number) {
        return res.status(400).json({ error: 'Укажите программу и день' });
      }

      const enrollment = await findEnrollment(user.id, program_id);
      if (!enrollment) return res.status(403).json({ error: 'Нет доступа к программе' });

      const energyVal = Math.max(1, Math.min(5, Number(energy || 3)));

      const { data: existing } = await supabase
        .from('tracker')
        .select('*')
        .eq('user_id', user.id)
        .eq('program_id', program_id)
        .eq('day_number', day_number)
        .limit(1);

      const payload = {
        mood: mood || 'calm',
        energy: energyVal,
        note: note || '',
        logged_at: new Date().toISOString(),
      };

      if (existing?.[0]) {
        const { data, error } = await supabase
          .from('tracker')
          .update(payload)
          .eq('id', existing[0].id)
          .select()
          .single();
        if (error) throw error;
        return res.status(200).json(data);
      }

      const { data, error } = await supabase
        .from('tracker')
        .insert({
          user_id: user.id,
          program_id,
          day_number,
          ...payload,
        })
        .select()
        .single();
      if (error) throw error;
      return res.status(201).json(data);
    }

    res.status(405).json({ error: 'Method not allowed' });
  } catch (err) {
    console.error('tracker error:', err);
    res.status(500).json({ error: err.message });
  }
}

import supabase from '../lib/db-client.js';
import { setCors } from '../lib/utils.js';

export default async function handler(req, res) {
  setCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();

  try {
    if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

    const { email, name, program_slug } = req.body || {};
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return res.status(400).json({ error: 'Укажите корректный email' });
    }

    const { data, error } = await supabase
      .from('waitlist')
      .insert({
        email: String(email).trim().toLowerCase(),
        name: (name || '').trim(),
        program_slug: program_slug || 'challenge-21',
      })
      .select()
      .single();
    if (error) throw error;
    return res.status(201).json(data);
  } catch (err) {
    console.error('waitlist error:', err);
    res.status(500).json({ error: err.message });
  }
}

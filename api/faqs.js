import supabase from './db-client.js';
import { setCors } from './utils.js';

export default async function handler(req, res) {
  setCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();

  try {
    if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });
    const { data, error } = await supabase
      .from('faqs')
      .select('*')
      .order('sort_order', { ascending: true });
    if (error) throw error;
    return res.status(200).json(data || []);
  } catch (err) {
    console.error('faqs error:', err);
    res.status(500).json({ error: err.message });
  }
}

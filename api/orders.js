import supabase from './db-client.js';
import { setCors, getUserFromReq } from './utils.js';

export default async function handler(req, res) {
  setCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();

  try {
    if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });
    const user = await getUserFromReq(req);
    if (!user) return res.status(401).json({ error: 'Нужна авторизация' });

    const { data, error } = await supabase
      .from('orders')
      .select('*')
      .eq('user_id', user.id)
      .order('id', { ascending: false });
    if (error) throw error;
    return res.status(200).json(data || []);
  } catch (err) {
    console.error('orders error:', err);
    res.status(500).json({ error: err.message });
  }
}

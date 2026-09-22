import supabase from '../lib/db-client.js';
import { setCors, getUserFromReq } from '../lib/utils.js';
import { mapCourse, accessUntil } from '../lib/mappers.js';

export default async function handler(req, res) {
  setCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();
  try {
    if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

    const user = await getUserFromReq(req);
    if (!user) return res.status(401).json({ error: 'Нужна авторизация' });

    const { data: purchases, error } = await supabase
      .from('course_purchases')
      .select('*')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false });
    if (error) throw error;

    const courseIds = [...new Set((purchases || []).map((p) => p.course_id))];
    let courses = [];
    if (courseIds.length) {
      const { data: cs } = await supabase.from('courses').select('*').in('id', courseIds);
      courses = cs || [];
    }

    const mapped = (purchases || []).map((p) => {
      const course = courses.find((c) => c.id === p.course_id);
      const program = course ? mapCourse(course) : null;
      const tariff = program?.tariffs?.[0] ?? null;
      return {
        id: p.id,
        user_id: p.user_id,
        program_id: p.course_id,
        tariff_id: tariff?.id ?? null,
        order_id: null,
        access_until: accessUntil(p.paid_at, course?.duration_days),
        created_at: p.created_at,
        program,
        tariff,
      };
    });

    return res.status(200).json(mapped);
  } catch (err) {
    console.error('enrollments error:', err);
    res.status(500).json({ error: err.message });
  }
}

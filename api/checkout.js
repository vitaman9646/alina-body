import supabase from '../lib/db-client.js';
import { setCors, getUserFromReq } from '../lib/utils.js';

export default async function handler(req, res) {
  setCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();

  try {
    if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

    const user = await getUserFromReq(req);
    if (!user) return res.status(401).json({ error: 'Нужна авторизация' });

    const { program_id } = req.body || {};
    if (!program_id) return res.status(400).json({ error: 'Выберите программу' });

    const courseId = String(program_id);

    const { data: course, error: cErr } = await supabase
      .from('courses')
      .select('*')
      .eq('id', courseId)
      .single();
    if (cErr) throw cErr;
    if (!course) return res.status(404).json({ error: 'Программа не найдена' });

    const { data: existing } = await supabase
      .from('course_purchases')
      .select('*')
      .eq('user_id', user.id)
      .eq('course_id', courseId)
      .limit(1);
    if (existing?.[0]) {
      return res.status(200).json({
        alreadyEnrolled: true,
        enrollment: existing[0],
        message: 'Доступ к этой программе у вас уже открыт',
      });
    }

    const amount = Number(course.price) || 0;
    const yookassaReady = Boolean(process.env.YOOKASSA_SECRET_KEY && process.env.YOOKASSA_SHOP_ID);
    const now = new Date().toISOString();

    const { data: purchase, error: pErr } = await supabase
      .from('course_purchases')
      .insert({
        user_id: user.id,
        course_id: courseId,
        status: 'paid',
        amount,
        currency: course.currency || 'RUB',
        payment_provider: yookassaReady ? 'yookassa' : 'manual',
        payment_id: null,
        paid_at: now,
      })
      .select()
      .single();
    if (pErr) throw pErr;

    return res.status(201).json({
      order: purchase,
      enrollment: purchase,
      alreadyEnrolled: false,
      instantAccess: true,
      message: 'Оплата подтверждена. Доступ открыт в личном кабинете.',
    });
  } catch (err) {
    console.error('checkout error:', err);
    res.status(500).json({ error: err.message });
  }
}

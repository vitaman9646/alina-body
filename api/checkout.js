import supabase from './db-client.js';
import { setCors, getUserFromReq, findEnrollment, addDays } from './utils.js';

export default async function handler(req, res) {
  setCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();

  try {
    if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

    const user = await getUserFromReq(req);
    if (!user) return res.status(401).json({ error: 'Нужна авторизация' });

    const { program_id, tariff_id } = req.body || {};
    if (!program_id || !tariff_id) {
      return res.status(400).json({ error: 'Выберите программу и тариф' });
    }

    const { data: program, error: pErr } = await supabase
      .from('programs')
      .select('*')
      .eq('id', program_id)
      .single();
    if (pErr) throw pErr;
    if (!program) return res.status(404).json({ error: 'Программа не найдена' });

    const { data: tariff, error: tErr } = await supabase
      .from('tariffs')
      .select('*')
      .eq('id', tariff_id)
      .single();
    if (tErr) throw tErr;
    if (!tariff || tariff.program_id !== program.id) {
      return res.status(400).json({ error: 'Тариф недоступен для этой программы' });
    }

    const existing = await findEnrollment(user.id, program.id);
    if (existing) {
      return res.status(200).json({
        alreadyEnrolled: true,
        enrollment: existing,
        message: 'Доступ к этой программе у вас уже открыт',
      });
    }

    const amount = Number(tariff.price);
    const yookassaReady = Boolean(process.env.YOOKASSA_SECRET_KEY && process.env.YOOKASSA_SHOP_ID);

    const { data: order, error: oErr } = await supabase
      .from('orders')
      .insert({
        user_id: user.id,
        user_email: user.email || '',
        program_id: program.id,
        tariff_id: tariff.id,
        amount,
        status: yookassaReady ? 'pending' : 'paid',
        payment_method: yookassaReady ? 'yookassa' : 'yookassa_ready',
      })
      .select()
      .single();
    if (oErr) throw oErr;

    if (yookassaReady) {
      return res.status(201).json({
        order,
        paymentUrl: null,
        message: 'Платёж ЮKassa будет подключён после добавления ключей',
      });
    }

    const { data: enrollment, error: eErr } = await supabase
      .from('enrollments')
      .insert({
        user_id: user.id,
        program_id: program.id,
        tariff_id: tariff.id,
        order_id: order.id,
        access_until: addDays(tariff.access_days || 60),
      })
      .select()
      .single();
    if (eErr) throw eErr;

    return res.status(201).json({
      order,
      enrollment,
      alreadyEnrolled: false,
      instantAccess: true,
      message: 'Оплата подтверждена. Доступ открыт в личном кабинете.',
    });
  } catch (err) {
    console.error('checkout error:', err);
    res.status(500).json({ error: err.message });
  }
}

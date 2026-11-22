import { createHash } from 'crypto';
import supabase from '../lib/db-client.js';
import { setCors, getUserFromReq } from '../lib/utils.js';

const NICEPAY_API = 'https://nicepay.io/public/api/payment';
const MERCHANT_ID = process.env.NICEPAY_MERCHANT_ID;
const SECRET = process.env.NICEPAY_SECRET;

function sha256hex(s) {
  return createHash('sha256').update(s, 'utf8').digest('hex');
}

// Подпись вебхука NicePay: sha256( сортированные_по_алфавиту "key=value" через "{np}" + "{np}" + secret ).
// ⚠️ Точный формат (key=value vs только value, состав параметров) сверить по реальному тестовому вебхуку
// или докам NicePay ДО продакшена — если промахнёмся, вебхук будет отклонять оплаты.
// `action` и `hash` исключаем: `hash` — сама подпись, `action` — наш роутинг-параметр из rewrite в vercel.json.
function verifyNicePayHash(params) {
  const keys = Object.keys(params)
    .filter((k) => k !== 'hash' && k !== 'action' && params[k] !== undefined && params[k] !== '')
    .sort();
  const joined = keys.map((k) => `${k}=${params[k]}`).join('{np}');
  const computed = sha256hex(joined + '{np}' + SECRET);
  return computed.toLowerCase() === String(params.hash || '').toLowerCase();
}

async function handleWebhook(req, res) {
  if (!SECRET) return res.status(500).send('not configured');

  if (!verifyNicePayHash(req.query || {})) {
    console.error('nicepay webhook: bad hash', JSON.stringify(req.query || {}));
    return res.status(400).send('bad signature');
  }

  const orderId = String(req.query.order_id || '');
  const result = String(req.query.result || '');
  const paymentId = String(req.query.payment_id || '');

  if (!orderId) return res.status(400).send('missing order_id');

  const { data: purchase, error } = await supabase
    .from('course_purchases')
    .select('id')
    .eq('id', orderId)
    .single();
  if (error || !purchase) {
    console.error('nicepay webhook: purchase not found', orderId);
    return res.status(404).send('not found');
  }

  if (result === 'success') {
    await supabase
      .from('course_purchases')
      .update({ status: 'paid', payment_id: paymentId || null, paid_at: new Date().toISOString() })
      .eq('id', orderId);
  } else {
    // финальный отказ/просрочка → cancelled (enum purchase_status: pending/paid/cancelled/refunded)
    await supabase
      .from('course_purchases')
      .update({ status: 'cancelled', payment_id: paymentId || null })
      .eq('id', orderId);
  }

  return res.status(200).send('OK');
}

export default async function handler(req, res) {
  setCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();

  try {
    // Вебхук: rewrite /api/nicepay → /api/checkout?action=webhook
    if (req.method === 'GET' && req.query?.action === 'webhook') {
      return await handleWebhook(req, res);
    }

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
      .eq('status', 'paid')
      .limit(1);
    if (existing?.[0]) {
      return res.status(200).json({
        alreadyEnrolled: true,
        enrollment: existing[0],
        message: 'Доступ к этой программе у вас уже открыт',
      });
    }

    const amount = Number(course.price) || 0;
    if (amount <= 0) return res.status(400).json({ error: 'Некорректная цена курса' });
    // Лимит Platega: одна транзакция ≤ 10 000 ₽
    if (amount > 10000) return res.status(400).json({ error: 'Максимальная сумма одной покупки — 10 000 ₽' });

    // pending-покупка; order_id для NicePay = id этой строки (вебхук мапит обратно)
    const { data: purchase, error: pErr } = await supabase
      .from('course_purchases')
      .insert({
        user_id: user.id,
        course_id: courseId,
        status: 'pending',
        amount,
        currency: course.currency || 'RUB',
        payment_provider: 'nicepay',
      })
      .select()
      .single();
    if (pErr) throw pErr;

    if (!MERCHANT_ID || !SECRET) {
      return res.status(500).json({ error: 'Платёжный провайдер не настроен' });
    }

    const proto = req.headers['x-forwarded-proto'] || 'https';
    const origin = `${proto}://${req.headers.host}`;
    const body = {
      merchant_id: MERCHANT_ID,
      secret: SECRET,
      order_id: purchase.id, // UUID, ≤50 симв
      customer: (user.email || user.id).slice(0,50),
      amount: amount * 100, // копейки
      currency: 'RUB',
      description: (course.title || 'Курс').slice(0,150),
      success_url: `${origin}/learn/${course.slug}`,
      fail_url: `${origin}/course/${course.slug}`,
    };

    const resp = await fetch(NICEPAY_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const npData = await resp.json().catch(() => ({}));
    if (!resp.ok || npData?.status !== 'success' || !npData?.data?.link) {
      console.error('nicepay create payment error:', resp.status, JSON.stringify(npData).slice(0, 500));
      return res.status(502).json({ error: 'Не удалось создать платёж, попробуйте ещё раз' });
    }

    await supabase
      .from('course_purchases')
      .update({ payment_id: npData.data.payment_id })
      .eq('id', purchase.id);

    return res.status(201).json({
      order: { ...purchase, payment_id: npData.data.payment_id },
      alreadyEnrolled: false,
      payment_url: npData.data.link,
    });
  } catch (err) {
    console.error('checkout error:', err);
    res.status(500).json({ error: err.message });
  }
}

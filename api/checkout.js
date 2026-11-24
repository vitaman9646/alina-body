import supabase from '../lib/db-client.js';
import { setCors, getUserFromReq } from '../lib/utils.js';

// Platega.io — основная касса (заменила NicePay, тот в git-истории).
// Создание платежа: POST /v2/transaction/process, заголовки X-MerchantId + X-Secret.
// Колбэк: POST на /api/platega (rewrite → /api/checkout?action=platega),
// аутентификация по заголовку X-Secret, маппинг обратно по полю `payload`.
const PLATEGA_API = 'https://app.platega.io';
const PLATEGA_MERCHANT_ID = process.env.PLATEGA_MERCHANT_ID;
const PLATEGA_SECRET = process.env.PLATEGA_SECRET;

// Идемпотентно по payload (внутренний id покупки): Platega шлёт до 3 повторов,
// порядок доставки не гарантирован — опираемся на статус, не на очерёдность.
async function handlePlategaCallback(req, res) {
  if (!PLATEGA_SECRET) return res.status(500).send('not configured');
  if (req.headers['x-secret'] !== PLATEGA_SECRET) {
    console.error('platega callback: bad x-secret');
    return res.status(401).send('unauthorized');
  }

  const body = req.body || {};
  const payload = String(body.payload || ''); // наш внутренний id (course_purchases.id)
  const status = String(body.status || '');
  const txId = body.id || null; // Platega transactionId (uuid)

  if (!payload) return res.status(400).send('missing payload');

  const { data: purchase, error } = await supabase
    .from('course_purchases')
    .select('id,status')
    .eq('id', payload)
    .single();
  if (error || !purchase) {
    console.error('platega callback: purchase not found', payload);
    return res.status(404).send('not found');
  }

  if (status === 'CONFIRMED') {
    // платёж зачислен → выдаём доступ
    await supabase
      .from('course_purchases')
      .update({ status: 'paid', payment_id: txId, paid_at: new Date().toISOString() })
      .eq('id', payload);
  } else if (status === 'CANCELED') {
    // не понижаем уже оплаченное (CANCELED может прийти раньше/позже CONFIRMED)
    if (purchase.status === 'pending') {
      await supabase.from('course_purchases').update({ status: 'cancelled' }).eq('id', payload);
    }
  } else if (status === 'CHARGEBACKED') {
    // полный возврат → отзываем доступ
    await supabase.from('course_purchases').update({ status: 'refunded' }).eq('id', payload);
  }
  // PARTIALLY_REFUNDED → остаётся paid; DISPUTED → без изменений (деньги зарезервированы)

  return res.status(200).send('OK');
}

export default async function handler(req, res) {
  setCors(res);
  if (req.method === 'OPTIONS') return res.status(204).end();

  try {
    // Колбэк Platega: rewrite /api/platega → /api/checkout?action=platega
    if (req.method === 'POST' && req.query?.action === 'platega') {
      return await handlePlategaCallback(req, res);
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

    // unique(user_id, course_id) на course_purchases → проверяем ЛЮБУЮ покупку, не только paid
    const { data: existingRows } = await supabase
      .from('course_purchases')
      .select('*')
      .eq('user_id', user.id)
      .eq('course_id', courseId)
      .limit(1);
    const existing = existingRows?.[0];
    if (existing?.status === 'paid') {
      return res.status(200).json({
        alreadyEnrolled: true,
        enrollment: existing,
        message: 'Доступ к этой программе у вас уже открыт',
      });
    }

    const amount = Number(course.price) || 0;
    if (amount <= 0) return res.status(400).json({ error: 'Некорректная цена курса' });
    // Лимит Platega: одна транзакция ≤ 10 000 ₽
    if (amount > 10000) return res.status(400).json({ error: 'Максимальная сумма одной покупки — 10 000 ₽' });

    // unique(user_id, course_id): если есть pending/cancelled/refunded — переиспользуем строку,
    // иначе вставляем новую. payload для колбэка = id этой строки (вебхук мапит обратно).
    let purchase;
    if (existing) {
      const { data: upd, error: uErr } = await supabase
        .from('course_purchases')
        .update({
          status: 'pending',
          amount,
          currency: course.currency || 'RUB',
          payment_provider: 'platega',
          payment_id: null,
          paid_at: null,
        })
        .eq('id', existing.id)
        .select()
        .single();
      if (uErr) throw uErr;
      purchase = upd;
    } else {
      const { data: ins, error: pErr } = await supabase
        .from('course_purchases')
        .insert({
          user_id: user.id,
          course_id: courseId,
          status: 'pending',
          amount,
          currency: course.currency || 'RUB',
          payment_provider: 'platega',
        })
        .select()
        .single();
      if (pErr) throw pErr;
      purchase = ins;
    }

    if (!PLATEGA_MERCHANT_ID || !PLATEGA_SECRET) {
      return res.status(500).json({ error: 'Платёжный провайдер не настроен' });
    }

    const proto = req.headers['x-forwarded-proto'] || 'https';
    const origin = `${proto}://${req.headers.host}`;
    // amount в рублях (не копейки). metadata.user_email обязателен — id покупателя.
    const body = {
      paymentDetails: { amount, currency: 'RUB' },
      description: (course.title || 'Курс').slice(0, 150),
      return: `${origin}/learn/${course.slug}`,
      failedUrl: `${origin}/course/${course.slug}`,
      payload: purchase.id,
      metadata: { user_email: user.email || `${user.id}@gmail.com` },
    };

    const resp = await fetch(`${PLATEGA_API}/v2/transaction/process`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-MerchantId': PLATEGA_MERCHANT_ID,
        'X-Secret': PLATEGA_SECRET,
      },
      body: JSON.stringify(body),
    });
    const pData = await resp.json().catch(() => ({}));
    const payUrl = pData?.url || pData?.redirect;
    if (!resp.ok || !payUrl) {
      console.error('platega create payment error:', resp.status, JSON.stringify(pData).slice(0, 500));
      return res.status(502).json({ error: 'Не удалось создать платёж, попробуйте ещё раз' });
    }

    await supabase
      .from('course_purchases')
      .update({ payment_id: pData.transactionId || null })
      .eq('id', purchase.id);

    return res.status(201).json({
      order: { ...purchase, payment_id: pData.transactionId },
      alreadyEnrolled: false,
      payment_url: payUrl,
    });
  } catch (err) {
    console.error('checkout error:', err);
    res.status(500).json({ error: err.message });
  }
}

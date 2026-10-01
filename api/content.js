import supabase from '../lib/db-client.js';

function html(title, message) {
  return `<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${title}</title>
</head>
<body style="font-family:system-ui,-apple-system,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;background:#FBF7F2;color:#3A312C;margin:0">
  <div style="text-align:center;padding:24px;max-width:420px">
    <h1 style="font-size:22px;margin:0 0 12px">${title}</h1>
    <p style="margin:0;color:#6B5E57;line-height:1.5">${message}</p>
  </div>
</body>
</html>`;
}

async function handleThreadsCallback(req, res) {
  const { code, error, error_description } = req.query;

  if (error) {
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    return res.status(400).send(html('Ошибка авторизации', error_description || error));
  }
  if (!code) {
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    return res.status(400).send(html('Ошибка авторизации', 'Не получен код авторизации.'));
  }

  try {
    const { error: insErr } = await supabase
      .from('oauth_temp_codes')
      .insert({ provider: 'threads', code: String(code) });
    if (insErr) throw insErr;

    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    return res.status(200).send(html('Готово', 'Авторизация получена, можно закрыть вкладку.'));
  } catch (e) {
    console.error('threads callback error:', e);
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    return res.status(500).send(html('Ошибка', 'Не удалось сохранить код авторизации.'));
  }
}

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  if (req.method === 'OPTIONS') return res.status(204).end();

  // Threads OAuth callback (не трогает остальные маршруты)
  if (req.query.provider === 'threads' && req.query.action === 'callback') {
    return handleThreadsCallback(req, res);
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  return res.status(200).json([]);
}

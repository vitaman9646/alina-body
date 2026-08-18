import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button, Eyebrow, Section } from '../components/ui';
import { useAuth } from '../contexts/AuthContext';
import supabase from '../lib/supabase';
import { signInWithGoogle } from '../lib/googleAuth';

export default function Auth() {
  const { user, loading } = useAuth();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const next = params.get('next') || '/dashboard';
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!loading && user) navigate(next, { replace: true });
  }, [user, loading, navigate, next]);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setInfo('');
    if (!email.trim() || !password) {
      setError('Введите email и пароль');
      return;
    }
    if (password.length < 6) {
      setError('Пароль должен быть не короче 6 символов');
      return;
    }
    setBusy(true);
    try {
      if (isSignUp) {
        const { error: err } = await supabase.auth.signUp({ email, password });
        if (err) throw err;
        setInfo('Аккаунт создан. Можно входить.');
        setIsSignUp(false);
      } else {
        const { error: err } = await supabase.auth.signInWithPassword({ email, password });
        if (err) throw err;
        navigate(next, { replace: true });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не получилось войти');
    } finally {
      setBusy(false);
    }
  };

  return (
    <Section>
      <div className="mx-auto max-w-md">
        <Eyebrow>Личный кабинет</Eyebrow>
        <h1 className="font-display text-[44px] leading-tight">
          {isSignUp ? 'Создать аккаунт' : 'Войти'}
        </h1>
        <p className="mt-3 text-sm text-stone">
          После оплаты уроки открываются именно здесь. Видео — только онлайн.
        </p>

        <form onSubmit={submit} className="mt-8 space-y-3">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            className="w-full rounded-2xl border border-ink/10 bg-white px-4 py-3.5 text-sm outline-none focus:border-rose"
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Пароль"
            className="w-full rounded-2xl border border-ink/10 bg-white px-4 py-3.5 text-sm outline-none focus:border-rose"
          />
          {error && <p className="text-sm text-[#9a4b43]">{error}</p>}
          {info && <p className="text-sm text-stone">{info}</p>}
          <Button type="submit" disabled={busy} className="w-full">
            {busy ? 'Подождите…' : isSignUp ? 'Зарегистрироваться' : 'Войти'}
          </Button>
        </form>

        <div className="my-6 text-center text-[13px] text-muted">или</div>

        <button
          onClick={() => signInWithGoogle('Alina Body')}
          className="flex w-full items-center justify-center gap-2 rounded-full border border-ink/10 bg-white py-3.5 text-[13px] transition hover:border-ink/25"
        >
          <svg width="16" height="16" viewBox="0 0 48 48" aria-hidden>
            <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.2 8 3.1l5.7-5.7C34.2 6.1 29.4 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.7-.4-3.5z" />
            <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 16 19 12 24 12c3.1 0 5.8 1.2 8 3.1l5.7-5.7C34.2 6.1 29.4 4 24 4 16.3 4 9.6 8.3 6.3 14.7z" />
            <path fill="#4CAF50" d="M24 44c5.2 0 10-2 13.6-5.2l-6.3-5.3C29.2 35.2 26.7 36 24 36c-5.3 0-9.7-3.3-11.3-8l-6.5 5C9.5 39.6 16.2 44 24 44z" />
            <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-1.1 3.2-3.5 5.7-6.7 7.1l6.3 5.3C37.4 38.3 44 33 44 24c0-1.3-.1-2.7-.4-3.5z" />
          </svg>
          Войти через Google
        </button>

        <button
          onClick={() => {
            setIsSignUp((v) => !v);
            setError('');
            setInfo('');
          }}
          className="mt-6 w-full text-center text-[13px] text-stone underline underline-offset-4"
        >
          {isSignUp ? 'Уже есть аккаунт? Войти' : 'Нет аккаунта? Создать'}
        </button>

        <p className="mt-8 text-center text-xs text-muted">
          Демо: demo@alinabody.ru / password123
        </p>
      </div>
    </Section>
  );
}

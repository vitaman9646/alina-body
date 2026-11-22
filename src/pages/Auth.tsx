import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button, Eyebrow, Section } from '../components/ui';
import { useAuth } from '../contexts/AuthContext';
import supabase from '../lib/supabase';

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
        setInfo('Аккаунт создан. Проверьте почту — мы отправили ссылку для подтверждения.');
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
      </div>
    </Section>
  );
}

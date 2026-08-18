import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ShieldCheck } from 'lucide-react';
import { Button, ErrorNote, Eyebrow, Section, Skeleton } from '../components/ui';
import { useAuth } from '../contexts/AuthContext';
import { api, formatPrice, type Program } from '../lib/api';

export default function Checkout() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { user, token, loading: authLoading } = useAuth();
  const [programs, setPrograms] = useState<Program[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [programId, setProgramId] = useState(Number(params.get('program') || 0));
  const [tariffId, setTariffId] = useState(Number(params.get('tariff') || 0));
  const [agree, setAgree] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api<Program[]>('/api/programs');
      setPrograms(data);
      if (!programId && data[0]) setProgramId(data[0].id);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить тарифы');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const program = programs.find((p) => p.id === programId) || programs[0];
  const tariff = useMemo(() => {
    if (!program) return undefined;
    return program.tariffs.find((t) => t.id === tariffId) || program.tariffs[0];
  }, [program, tariffId]);

  useEffect(() => {
    if (program && tariff && tariff.id !== tariffId) setTariffId(tariff.id);
  }, [program, tariff, tariffId]);

  const pay = async () => {
    setFormError('');
    if (!user) {
      const next = encodeURIComponent(`/checkout?program=${program?.id}&tariff=${tariff?.id}`);
      navigate(`/auth?next=${next}`);
      return;
    }
    if (!agree) {
      setFormError('Подтвердите согласие с офертой');
      return;
    }
    if (!program || !tariff) return;
    setSubmitting(true);
    try {
      const result = await api<{ alreadyEnrolled?: boolean; instantAccess?: boolean; message?: string }>(
        '/api/checkout',
        {
          method: 'POST',
          token,
          body: JSON.stringify({ program_id: program.id, tariff_id: tariff.id }),
        }
      );
      navigate('/dashboard', { state: { notice: result.message } });
    } catch (e) {
      setFormError(e instanceof Error ? e.message : 'Оплата не прошла');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading || authLoading) {
    return (
      <Section>
        <Skeleton className="h-[60vh]" />
      </Section>
    );
  }
  if (error) {
    return (
      <Section>
        <ErrorNote message={error} onRetry={load} />
      </Section>
    );
  }

  return (
    <Section>
      <div className="mx-auto max-w-3xl">
        <Eyebrow>Оформление</Eyebrow>
        <h1 className="font-display text-[44px] leading-tight sm:text-[56px]">Безопасная оплата</h1>
        <p className="mt-3 text-sm text-stone">Оплата проходит через ЮKassa. После подтверждения доступ открывается сразу.</p>

        <div className="mt-10 space-y-4">
          <div className="grid gap-3 sm:grid-cols-2">
            {programs.map((p) => (
              <button
                key={p.id}
                onClick={() => {
                  setProgramId(p.id);
                  setTariffId(p.tariffs[0]?.id || 0);
                }}
                className={`rounded-[24px] border px-5 py-4 text-left ${
                  program?.id === p.id ? 'border-ink bg-white' : 'border-ink/10 bg-white/50'
                }`}
              >
                <p className="text-[11px] uppercase tracking-[0.18em] text-rose">{p.short_title}</p>
                <p className="mt-1 font-display text-[24px] leading-tight">{p.title}</p>
              </button>
            ))}
          </div>

          {program && (
            <div className="grid gap-3 md:grid-cols-3">
              {program.tariffs.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setTariffId(t.id)}
                  className={`rounded-[24px] border px-5 py-5 text-left ${
                    tariff?.id === t.id ? 'border-ink bg-cream' : 'border-ink/10 bg-white'
                  }`}
                >
                  <p className="text-[12px] uppercase tracking-[0.16em] text-rose">{t.name}</p>
                  <p className="mt-2 font-display text-[28px]">{formatPrice(t.price)}</p>
                  <p className="mt-2 text-xs text-muted">{t.access_days} дней доступа</p>
                </button>
              ))}
            </div>
          )}
        </div>

        {tariff && program && (
          <div className="mt-8 rounded-[28px] bg-white p-7 shadow-[0_16px_40px_-30px_rgba(58,49,44,0.45)]">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm text-muted">{program.title}</p>
                <p className="font-display text-[28px]">Тариф {tariff.name}</p>
              </div>
              <p className="font-display text-[32px]">{formatPrice(tariff.price)}</p>
            </div>
            <ul className="mt-5 space-y-2 text-sm text-stone">
              {tariff.features.map((f) => (
                <li key={f}>— {f}</li>
              ))}
            </ul>
            <label className="mt-6 flex items-start gap-3 text-sm text-stone">
              <input type="checkbox" checked={agree} onChange={(e) => setAgree(e.target.checked)} className="mt-1" />
              <span>
                Я принимаю <a className="underline" href="/terms">оферту</a> и{' '}
                <a className="underline" href="/privacy">политику конфиденциальности</a>
              </span>
            </label>
            {formError && <p className="mt-3 text-sm text-[#9a4b43]">{formError}</p>}
            <Button onClick={pay} disabled={submitting} className="mt-6 w-full">
              {submitting ? 'Подтверждаем…' : user ? 'Оплатить через ЮKassa' : 'Войти и оплатить'}
            </Button>
            <p className="mt-4 flex items-center justify-center gap-2 text-xs text-muted">
              <ShieldCheck size={14} /> Защищённый платёж. Видео откроются в кабинете сразу после оплаты.
            </p>
          </div>
        )}
      </div>
    </Section>
  );
}

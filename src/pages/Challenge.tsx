import { useEffect, useState, type FormEvent } from 'react';
import { Check } from 'lucide-react';
import { ButtonLink, ErrorNote, Eyebrow, FadeIn, Section, Skeleton } from '../components/ui';
import { api, formatPrice, type Program } from '../lib/api';

export default function Challenge() {
  const [program, setProgram] = useState<Program | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [sent, setSent] = useState(false);
  const [formError, setFormError] = useState('');
  const [sending, setSending] = useState(false);

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api<Program>('/api/programs?slug=challenge-21');
      setProgram(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить программу');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const joinWaitlist = async (e: FormEvent) => {
    e.preventDefault();
    setFormError('');
    if (!email.trim()) {
      setFormError('Укажите email');
      return;
    }
    setSending(true);
    try {
      await api('/api/waitlist', {
        method: 'POST',
        body: JSON.stringify({ email, name, program_slug: 'challenge-21' }),
      });
      setSent(true);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Не получилось отправить');
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <Section>
        <Skeleton className="h-[70vh]" />
      </Section>
    );
  }

  if (error || !program) {
    return (
      <Section>
        <ErrorNote message={error || 'Программа не найдена'} onRetry={load} />
      </Section>
    );
  }

  const tariff = program.tariffs[0];

  return (
    <div>
      <Section className="pb-10">
        <div className="grid items-center gap-12 lg:grid-cols-2">
          <FadeIn>
            <Eyebrow>Челлендж</Eyebrow>
            <h1 className="font-display text-[46px] leading-[0.98] sm:text-[64px]">{program.title}</h1>
            <p className="mt-6 max-w-lg text-[16px] leading-relaxed text-stone">{program.description}</p>
            <p className="mt-4 text-sm text-muted">
              {program.next_start}. {program.seats_note}.
            </p>
            <div className="mt-8 flex flex-wrap items-end gap-6">
              <div>
                <p className="text-[11px] uppercase tracking-[0.2em] text-rose">Стоимость</p>
                <p className="font-display text-[44px] leading-none">{formatPrice(program.price)}</p>
              </div>
              {tariff && (
                <ButtonLink to={`/checkout?program=${program.id}&tariff=${tariff.id}`}>
                  Записаться на поток
                </ButtonLink>
              )}
            </div>
          </FadeIn>
          <FadeIn delay={0.08}>
            <img
              src={program.image_url}
              alt={program.title}
              className="aspect-[4/5] w-full rounded-[36px] object-cover shadow-[0_30px_70px_-30px_rgba(92,64,56,0.4)]"
            />
          </FadeIn>
        </div>
      </Section>

      <Section className="bg-[#F3EBE3]/50">
        <div className="grid gap-10 md:grid-cols-2">
          <div>
            <Eyebrow>Что внутри</Eyebrow>
            <h2 className="font-display text-[40px] leading-tight">Мягкий вход без перегруза</h2>
          </div>
          <ul className="space-y-4">
            {program.highlights.map((h) => (
              <li key={h} className="flex gap-3 rounded-[22px] bg-white px-5 py-4 text-sm">
                <Check size={16} className="mt-0.5 text-rose" /> {h}
              </li>
            ))}
          </ul>
        </div>
      </Section>

      <Section>
        <div className="grid gap-10 lg:grid-cols-2">
          <div>
            <Eyebrow>Следующий поток</Eyebrow>
            <h2 className="font-display text-[40px] leading-tight">Оставьте email — напомним о старте</h2>
            <p className="mt-4 max-w-md text-sm leading-relaxed text-stone">
              Количество мест ограничено. Мы напишем спокойно и один раз, когда откроется запись.
            </p>
          </div>
          <div className="rounded-[28px] border border-ink/6 bg-white p-7">
            {sent ? (
              <p className="font-display text-[28px] leading-snug">Спасибо. Мы бережно сохранили ваш адрес.</p>
            ) : (
              <form onSubmit={joinWaitlist} className="space-y-4">
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Имя"
                  className="w-full rounded-2xl border border-ink/10 bg-cream px-4 py-3.5 text-sm outline-none focus:border-rose"
                />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Email"
                  className="w-full rounded-2xl border border-ink/10 bg-cream px-4 py-3.5 text-sm outline-none focus:border-rose"
                />
                {formError && <p className="text-sm text-[#9a4b43]">{formError}</p>}
                <button
                  disabled={sending}
                  className="w-full rounded-full bg-ink py-3.5 text-[13px] text-cream disabled:opacity-50"
                >
                  {sending ? 'Отправляем…' : 'Сообщить о старте'}
                </button>
              </form>
            )}
          </div>
        </div>
      </Section>
    </div>
  );
}

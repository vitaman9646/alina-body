import { useEffect, useState } from 'react';
import { Check } from 'lucide-react';
import { ButtonLink, ErrorNote, Eyebrow, FadeIn, Section, Skeleton } from '../components/ui';
import { api, formatPrice, type Program } from '../lib/api';

export default function Course() {
  const [program, setProgram] = useState<Program | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api<Program>('/api/programs?slug=transformation-8');
      setProgram(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить курс');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

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
        <ErrorNote message={error || 'Курс не найден'} onRetry={load} />
      </Section>
    );
  }

  return (
    <div>
      <Section className="pb-10">
        <div className="grid items-center gap-12 lg:grid-cols-2">
          <FadeIn>
            <Eyebrow>Основной курс</Eyebrow>
            <h1 className="font-display text-[46px] leading-[0.98] sm:text-[64px]">{program.title}</h1>
            <p className="mt-6 max-w-lg text-[16px] leading-relaxed text-stone">{program.description}</p>
            <p className="mt-5 text-sm text-muted">{program.tagline}</p>
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
        <Eyebrow>Что входит</Eyebrow>
        <h2 className="max-w-xl font-display text-[40px] leading-tight">Тело, ягодицы, пресс, осанка — в одном ритме</h2>
        <div className="mt-10 grid gap-3 sm:grid-cols-2">
          {program.highlights.map((h) => (
            <div key={h} className="flex gap-3 rounded-[22px] bg-white px-5 py-4 text-sm">
              <Check size={16} className="mt-0.5 text-rose" /> {h}
            </div>
          ))}
        </div>
      </Section>

      <Section>
        <Eyebrow>Тарифы</Eyebrow>
        <h2 className="font-display text-[40px] leading-tight">Выберите глубину сопровождения</h2>
        <div className="mt-10 grid gap-5 lg:grid-cols-3">
          {program.tariffs.map((t) => (
            <article
              key={t.id}
              className={`flex h-full flex-col rounded-[28px] p-7 ${
                t.is_popular ? 'bg-ink text-cream' : 'border border-ink/8 bg-white'
              }`}
            >
              <p className={`text-[11px] uppercase tracking-[0.2em] ${t.is_popular ? 'text-blush' : 'text-rose'}`}>
                {t.name}
                {t.is_popular ? ' · чаще выбирают' : ''}
              </p>
              <p className="mt-4 font-display text-[40px] leading-none">{formatPrice(t.price)}</p>
              <p className={`mt-3 text-sm ${t.is_popular ? 'text-cream/70' : 'text-stone'}`}>{t.description}</p>
              <ul className="mt-6 flex-1 space-y-2.5 text-sm">
                {t.features.map((f) => (
                  <li key={f} className="flex gap-2">
                    <Check size={15} className={t.is_popular ? 'text-blush' : 'text-rose'} />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
              <div className="mt-8">
                <ButtonLink
                  to={`/checkout?program=${program.id}&tariff=${t.id}`}
                  variant={t.is_popular ? 'soft' : 'primary'}
                  className="w-full"
                >
                  Выбрать {t.name}
                </ButtonLink>
              </div>
            </article>
          ))}
        </div>
      </Section>
    </div>
  );
}

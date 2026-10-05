import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Check } from 'lucide-react';
import { ErrorNote, Eyebrow, FadeIn, Section, Skeleton } from '../components/ui';
import { api, formatPrice } from '../lib/api';
import Seo from '../components/Seo';

// Тип темы — одна тема тела/цели = одна пара «трипваер → мини-курс»
type Theme = {
  id: string;
  slug: string;
  title: string;
  voiceLine: string;
  tripwire: {
    title: string;
    days: number;
    minutesPerDay: number;
    price: number;
    slug: string;
    image: string;
  };
  course: {
    title: string;
    days: number;
    price: number;
    slug: string;
    image: string;
  };
};

// Цветовой акцент каждой зоны тела — пастель, в духе «мягкой силы»
const ZONES: Record<string, { accent: string; soft: string; label: string }> = {
  'glutes-legs': { accent: '#C47A8B', soft: '#F2DCE1', label: 'Ягодицы и ноги' },
  'core-abs': { accent: '#93A98A', soft: '#E2EAD9', label: 'Кор и пресс' },
  'arms-back': { accent: '#A99BC4', soft: '#E9E3F2', label: 'Руки и спина' },
  'posture-full': { accent: '#A7BFCB', soft: '#E1EBF1', label: 'Осанка и всё тело' },
  mobility: { accent: '#D9B36C', soft: '#F4E9D2', label: 'Мобильность и растяжка' },
};

function zoneOf(slug: string) {
  return ZONES[slug] || { accent: '#C9A299', soft: '#F3E7E2', label: '' };
}

// Картинка с градиентной подложкой: если фото нет (404) — остаётся цвет зоны
function ZoneImage({ src, alt, zone }: { src: string; alt: string; zone: { accent: string; soft: string } }) {
  return (
    <div
      className="relative h-48 w-full overflow-hidden"
      style={{ background: `linear-gradient(135deg, ${zone.soft}, ${zone.accent})` }}
    >
      <img
        src={src}
        alt={alt}
        onError={(e) => {
          (e.currentTarget as HTMLImageElement).style.display = 'none';
        }}
        className="h-full w-full object-cover"
      />
    </div>
  );
}

function ThemeSection({ theme, index }: { theme: Theme; index: number }) {
  const zone = zoneOf(theme.slug);
  return (
    <FadeIn delay={index * 0.05}>
      <div className="overflow-hidden rounded-[36px] border border-ink/6 bg-white/60" style={{ boxShadow: `0 20px 50px -32px ${zone.accent}55` }}>
        <div className="h-1.5 w-full" style={{ background: zone.accent }} />
        <div className="p-6 md:p-10">
          <div className="max-w-xl">
            <Eyebrow>{theme.title}</Eyebrow>
            <p className="font-display text-[22px] italic leading-snug text-ink">
              «{theme.voiceLine}»
            </p>
          </div>

          <div className="mt-10 grid gap-6 md:grid-cols-[1fr_auto_1.15fr] md:items-stretch">
            <Link
              to={`/tonus-doma/${theme.tripwire.slug}`}
              className="group overflow-hidden rounded-[28px] border border-sand bg-milk transition-colors hover:border-clay"
            >
              <ZoneImage src={theme.tripwire.image} alt={theme.tripwire.title} zone={zone} />
              <div className="p-6">
                <p className="text-[11px] uppercase tracking-[0.22em]" style={{ color: zone.accent }}>Попробовать</p>
                <h3 className="mt-2 font-display text-[26px] leading-tight">{theme.tripwire.title}</h3>
                <p className="mt-2 text-sm text-stone">
                  {theme.tripwire.days} дня · {theme.tripwire.minutesPerDay} минут в день
                </p>
                <p className="mt-4 font-display text-[28px]">{formatPrice(theme.tripwire.price)}</p>
              </div>
            </Link>

            <div className="hidden items-center justify-center md:flex">
              <div className="h-px w-10" style={{ background: `linear-gradient(to right, ${zone.soft}, ${zone.accent})` }} />
            </div>
            <div className="flex items-center justify-center md:hidden">
              <div className="h-10 w-px" style={{ background: `linear-gradient(to bottom, ${zone.soft}, ${zone.accent})` }} />
            </div>

            <Link
              to={`/tonus-doma/${theme.course.slug}`}
              className="group overflow-hidden rounded-[28px] transition-transform hover:-translate-y-0.5"
              style={{ background: zone.soft }}
            >
              <ZoneImage src={theme.course.image} alt={theme.course.title} zone={zone} />
              <div className="p-6">
                <p className="text-[11px] uppercase tracking-[0.22em] text-stone">Продолжить</p>
                <h3 className="mt-2 font-display text-[26px] leading-tight">{theme.course.title}</h3>
                <p className="mt-2 text-sm text-stone">Полная программа зоны · {theme.course.days} дней</p>
                <div className="mt-4 flex items-center justify-between">
                  <p className="font-display text-[28px]">{formatPrice(theme.course.price)}</p>
                  <span
                    className="inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-[13px] font-medium text-cream"
                    style={{ background: zone.accent }}
                  >
                    Открыть <ArrowRight size={14} />
                  </span>
                </div>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </FadeIn>
  );
}

export default function TonusDoma() {
  const [themes, setThemes] = useState<Theme[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api<Theme[]>('/api/mini-course-themes');
      setThemes(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить темы');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div>
      <Seo
        title="Мини-курсы — Alina Body"
        description="Короткие домашние мини-курсы по зонам тела: 3–7 дней, 15–20 минут в день. Начните с малого шага."
        path="/tonus-doma"
      />
      <Section className="pt-16 pb-10">
        <FadeIn>
          <Eyebrow>Мини-курсы</Eyebrow>
          <h1 className="max-w-2xl font-display text-[44px] leading-[1.05] sm:text-[58px]">
            Короткие программы <span className="italic">под свою цель</span>
          </h1>
          <p className="mt-6 max-w-xl text-[16px] leading-relaxed text-stone">
            Начните с малого шага — 3 дня, 15 минут — и продолжайте, когда почувствуете,
            что готовы идти глубже.
          </p>
        </FadeIn>
      </Section>

      <Section className="space-y-8 pt-0">
        {loading ? (
          <Skeleton className="h-96" />
        ) : error ? (
          <ErrorNote message={error} onRetry={load} />
        ) : (
          themes.map((theme, i) => (
            <ThemeSection key={theme.id} theme={theme} index={i} />
          ))
        )}
      </Section>

      <Section className="bg-[#F3EBE3]/50">
        <div className="mx-auto max-w-lg text-center">
          <Eyebrow>Готовы больше?</Eyebrow>
          <h2 className="font-display text-[32px] leading-tight sm:text-[38px]">
            Если захотите собрать всё <span className="italic">в единую систему</span>
          </h2>
          <p className="mt-4 text-sm leading-relaxed text-stone">
            Оставьте почту — расскажем, когда будет готово, и первыми покажем новые темы.
          </p>
          <form className="mt-7 flex flex-col gap-3 sm:flex-row sm:justify-center">
            <input
              type="email"
              required
              placeholder="Ваша почта"
              className="rounded-full border border-ink/15 bg-white px-6 py-3.5 text-sm text-ink outline-none focus:border-clay sm:w-72"
            />
            <button
              type="submit"
              className="inline-flex items-center justify-center gap-1.5 rounded-full bg-ink px-7 py-3.5 text-[13px] font-medium text-cream transition-colors hover:bg-[#2b241f]"
            >
              <Check size={14} /> Подписаться
            </button>
          </form>
        </div>
      </Section>
    </div>
  );
}

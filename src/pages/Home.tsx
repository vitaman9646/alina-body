import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Check, ChevronDown, Flower2, Heart, Sparkles, Wind } from 'lucide-react';
import { ButtonLink, ErrorNote, Eyebrow, FadeIn, Section, Skeleton } from '../components/ui';
import { api, formatPrice, type Faq, type Program, type Review } from '../lib/api';

const pains = [
  {
    title: 'Нет времени на зал',
    text: '20–30 минут дома. Без дороги, без очереди к тренажёрам, без чужого ритма.',
  },
  {
    title: 'Страх начать «не идеально»',
    text: 'Программы собраны так, чтобы можно было войти мягко — даже если давно не двигались.',
  },
  {
    title: 'Жёсткие ограничения утомляют',
    text: 'Никакой гонки и наказаний. Только устойчивый ритм, который можно удержать.',
  },
  {
    title: 'Результат не держится',
    text: 'Мы работаем с осанкой, дыханием и привычкой — чтобы тело оставалось собранным после курса.',
  },
];

const results = [
  {
    title: 'Лёгкость и энергия',
    text: 'Тело перестаёт казаться тяжёлым. Появляется ровное утро и спокойный тонус дня.',
    image: '/images/result-ease.jpg',
    icon: Wind,
  },
  {
    title: 'Подтянутый тонус',
    text: 'Мягкая плотность мышц, собранный кор и более ясный силуэт — без изнурения.',
    image: '/images/result-tone.jpg',
    icon: Sparkles,
  },
  {
    title: 'Уверенность в себе',
    text: 'Когда осанка выравнивается, меняется и ощущение себя. Это видно в зеркале и в походке.',
    image: '/images/result-confidence.jpg',
    icon: Heart,
  },
  {
    title: 'Здоровая привычка',
    text: 'Короткие занятия, которые встраиваются в жизнь. Не подвиг, а ежедневная забота.',
    image: '/images/result-habit.jpg',
    icon: Flower2,
  },
];

const steps = [
  { n: '01', title: 'Выбор программы', text: 'Челлендж на 21 день или полный курс на 8 недель. Спокойно сравните форматы и тарифы.' },
  { n: '02', title: 'Безопасная оплата', text: 'Оплата проходит через ЮKassa. Карта, СБП и привычные способы — без лишних шагов.' },
  { n: '03', title: 'Мгновенный доступ', text: 'Сразу после оплаты открывается личный кабинет. Уроки и PDF уже на месте.' },
  { n: '04', title: 'Онлайн-просмотр', text: 'Видео смотрятся только в кабинете. Скачать архив нельзя — так мы бережём материалы. PDF можно сохранить себе.' },
];

export default function Home() {
  const [programs, setPrograms] = useState<Program[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [faqs, setFaqs] = useState<Faq[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const [p, r, f] = await Promise.all([
        api<Program[]>('/api/programs'),
        api<Review[]>('/api/reviews'),
        api<Faq[]>('/api/faqs'),
      ]);
      setPrograms(p);
      setReviews(r);
      setFaqs(f);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить данные');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const challenge = programs.find((p) => p.type === 'challenge');
  const course = programs.find((p) => p.type === 'course');

  return (
    <div>
      <section className="relative overflow-hidden">
        <div className="mx-auto grid min-h-[calc(100vh-72px)] max-w-6xl items-center gap-10 px-5 py-10 sm:px-8 lg:grid-cols-[1.05fr_0.95fr] lg:gap-16">
          <FadeIn>
            <p className="mb-6 text-[11px] uppercase tracking-[0.32em] text-rose">Онлайн-фитнес · дом · 18–28</p>
            <h1 className="font-display text-[48px] leading-[0.95] tracking-[-0.02em] text-ink sm:text-[72px] lg:text-[84px]">
              Твоё тело —<br />
              <span className="italic font-medium">твоя эстетика</span>
            </h1>
            <p className="mt-7 max-w-md text-[16px] leading-relaxed text-stone sm:text-[17px]">
              Онлайн-программы для похудения, тонуса и лёгкой энергии без жёстких ограничений.
            </p>
            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <ButtonLink to="/#programs">Выбрать программу</ButtonLink>
              <ButtonLink to="/challenge" variant="ghost">
                Смотреть челлендж
              </ButtonLink>
            </div>
            <p className="mt-8 text-[13px] tracking-wide text-muted">
              6+ лет практики · 10 000+ уроков · мягкая сила без изнурения
            </p>
          </FadeIn>

          <FadeIn delay={0.12} className="relative">
            <div className="relative mx-auto max-w-[480px]">
              <div className="absolute -left-6 top-10 hidden h-28 w-28 rounded-full bg-blush/70 blur-2xl sm:block" />
              <div className="absolute -right-4 bottom-16 hidden h-24 w-24 rounded-full bg-sand/80 blur-2xl sm:block" />
              <img
                src="/images/hero-alina.jpg"
                alt="Алина — фитнес-тренер Alina Body"
                className="relative z-10 aspect-[3/4] w-full rounded-[36px] object-cover shadow-[0_30px_80px_-28px_rgba(92,64,56,0.35)]"
              />
              <div className="absolute -bottom-5 left-5 right-5 z-20 rounded-[22px] border border-white/60 bg-white/80 px-5 py-4 backdrop-blur-md sm:left-8 sm:right-auto">
                <p className="text-[11px] uppercase tracking-[0.2em] text-rose">Ближайший старт</p>
                <p className="mt-1 font-display text-[22px] italic">Челлендж 21 день</p>
                <p className="text-[13px] text-muted">следующий поток скоро стартует</p>
              </div>
            </div>
          </FadeIn>
        </div>
      </section>

      <Section id="challenge" className="pt-10">
        {loading ? (
          <Skeleton className="h-[420px]" />
        ) : error ? (
          <ErrorNote message={error} onRetry={load} />
        ) : challenge ? (
          <div className="grid items-center gap-10 overflow-hidden rounded-[36px] bg-[#F3EBE3] md:grid-cols-2">
            <img
              src={challenge.image_url || '/images/challenge-mood.jpg'}
              alt={challenge.title}
              className="h-full min-h-[320px] w-full object-cover md:min-h-[520px]"
            />
            <div className="px-7 py-10 md:px-12 md:py-14">
              <Eyebrow>Вход в практику</Eyebrow>
              <h2 className="font-display text-[40px] leading-[1.05] sm:text-[52px]">{challenge.title}</h2>
              <p className="mt-5 max-w-md text-[15px] leading-relaxed text-stone">{challenge.description}</p>
              <ul className="mt-7 space-y-3">
                {challenge.highlights.map((h) => (
                  <li key={h} className="flex items-start gap-3 text-sm text-ink">
                    <Check size={16} className="mt-0.5 shrink-0 text-rose" />
                    <span>{h}</span>
                  </li>
                ))}
              </ul>
              <div className="mt-8 flex flex-wrap items-end justify-between gap-5">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.2em] text-muted">Стоимость участия</p>
                  <p className="font-display text-[40px] leading-none">{formatPrice(challenge.price)}</p>
                  <p className="mt-2 text-[13px] text-muted">{challenge.seats_note}</p>
                </div>
                <ButtonLink to="/challenge">
                  Смотреть челлендж <ArrowRight size={15} className="ml-2" />
                </ButtonLink>
              </div>
            </div>
          </div>
        ) : null}
      </Section>

      <Section>
        <FadeIn>
          <Eyebrow>Почему это работает</Eyebrow>
          <h2 className="max-w-xl font-display text-[40px] leading-[1.05] sm:text-[52px]">
            Не сила воли. <span className="italic">Система заботы.</span>
          </h2>
        </FadeIn>
        <div className="mt-12 grid gap-4 sm:grid-cols-2">
          {pains.map((item, i) => (
            <FadeIn key={item.title} delay={i * 0.06}>
              <article className="h-full rounded-[28px] border border-ink/6 bg-white/70 p-7 shadow-[0_12px_40px_-28px_rgba(58,49,44,0.35)]">
                <p className="font-display text-[26px] leading-tight">{item.title}</p>
                <p className="mt-3 text-sm leading-relaxed text-stone">{item.text}</p>
              </article>
            </FadeIn>
          ))}
        </div>
      </Section>

      <Section id="programs" className="bg-[#F3EBE3]/60">
        <FadeIn>
          <Eyebrow>Программы</Eyebrow>
          <h2 className="font-display text-[40px] leading-[1.05] sm:text-[52px]">
            Выбери свой <span className="italic">ритм</span>
          </h2>
          <p className="mt-4 max-w-xl text-stone">
            Челлендж — мягкий вход. Восьминедельная трансформация — основной путь платформы.
          </p>
        </FadeIn>

        {loading ? (
          <div className="mt-12 grid gap-6 md:grid-cols-2">
            <Skeleton className="h-96" />
            <Skeleton className="h-96" />
          </div>
        ) : (
          <div className="mt-12 grid gap-6 md:grid-cols-2">
            {programs.map((p) => (
              <article key={p.id} className="overflow-hidden rounded-[32px] bg-white shadow-[0_20px_50px_-32px_rgba(58,49,44,0.4)]">
                <img src={p.image_url} alt={p.title} className="h-64 w-full object-cover" />
                <div className="p-7">
                  <p className="text-[11px] uppercase tracking-[0.22em] text-rose">{p.short_title}</p>
                  <h3 className="mt-2 font-display text-[32px] leading-tight">{p.title}</h3>
                  <p className="mt-3 text-sm leading-relaxed text-stone">{p.tagline}</p>
                  <div className="mt-6 flex items-end justify-between gap-4">
                    <div>
                      <p className="font-display text-[30px]">{formatPrice(p.price)}</p>
                      <p className="text-xs text-muted">{p.duration_label}</p>
                    </div>
                    <ButtonLink to={p.type === 'challenge' ? '/challenge' : '/course'} variant="soft">
                      Подробнее
                    </ButtonLink>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}

        {course && (
          <div className="mt-8 rounded-[32px] border border-ink/6 bg-white/80 p-7 md:p-10">
            <div className="flex flex-col justify-between gap-6 md:flex-row md:items-end">
              <div>
                <Eyebrow>Основной продукт</Eyebrow>
                <h3 className="font-display text-[34px] leading-tight">{course.title}</h3>
                <p className="mt-3 max-w-xl text-sm text-stone">{course.description}</p>
              </div>
              <ButtonLink to="/course">Смотреть тарифы</ButtonLink>
            </div>
            <div className="mt-8 grid gap-3 sm:grid-cols-3">
              {course.tariffs.map((t) => (
                <div key={t.id} className="rounded-[24px] bg-cream px-5 py-5">
                  <p className="text-[12px] uppercase tracking-[0.16em] text-rose">{t.name}</p>
                  <p className="mt-2 font-display text-[28px]">{formatPrice(t.price)}</p>
                  <p className="mt-2 text-xs leading-relaxed text-muted">{t.description}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </Section>

      <Section id="about">
        <div className="grid items-center gap-12 lg:grid-cols-[0.9fr_1.1fr]">
          <FadeIn>
            <div className="relative mx-auto max-w-md">
              <img
                src="/images/about-alina.jpg"
                alt="Алина, основательница Alina Body"
                className="aspect-[4/5] w-full rounded-[36px] object-cover shadow-[0_30px_70px_-30px_rgba(92,64,56,0.4)]"
              />
            </div>
          </FadeIn>
          <FadeIn delay={0.08}>
            <Eyebrow>Об Алине</Eyebrow>
            <h2 className="font-display text-[42px] leading-[1.05] sm:text-[54px]">
              Спокойный экспертный <span className="italic">голос тела</span>
            </h2>
            <p className="mt-6 max-w-xl text-[15px] leading-relaxed text-stone">
              Алина — фитнес-тренер с более чем 6 годами практики и 10 000+ проведённых уроков. Она работает с женщинами мягко: без крика, без изнурения, без обещаний «новой жизни за неделю».
            </p>
            <p className="mt-4 max-w-xl text-[15px] leading-relaxed text-stone">
              В основе подхода — осанка, дыхание, глубокий кор, суставы и устойчивый результат. Сила здесь тихая. Она собирает тело изнутри и оставляет ощущение лёгкости.
            </p>
            <div className="mt-8 grid grid-cols-3 gap-3">
              {[
                ['6+', 'лет практики'],
                ['10 000+', 'уроков'],
                ['18–28', 'возраст аудитории'],
              ].map(([n, l]) => (
                <div key={l} className="rounded-[22px] bg-cream px-3 py-4 text-center">
                  <p className="font-display text-[28px]">{n}</p>
                  <p className="text-[11px] text-muted">{l}</p>
                </div>
              ))}
            </div>
          </FadeIn>
        </div>
      </Section>

      <Section className="bg-[#F3EBE3]/50">
        <FadeIn>
          <Eyebrow>Результаты</Eyebrow>
          <h2 className="max-w-lg font-display text-[40px] leading-[1.05] sm:text-[52px]">
            Что остаётся <span className="italic">после практики</span>
          </h2>
        </FadeIn>
        <div className="mt-12 grid gap-5 sm:grid-cols-2">
          {results.map((r, i) => (
            <FadeIn key={r.title} delay={i * 0.05}>
              <article className="overflow-hidden rounded-[28px] bg-white">
                <img src={r.image} alt={r.title} className="h-56 w-full object-cover" />
                <div className="p-6">
                  <r.icon size={18} className="text-rose" />
                  <h3 className="mt-3 font-display text-[28px]">{r.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-stone">{r.text}</p>
                </div>
              </article>
            </FadeIn>
          ))}
        </div>
      </Section>

      <Section>
        <FadeIn>
          <Eyebrow>Как устроено обучение</Eyebrow>
          <h2 className="max-w-xl font-display text-[40px] leading-[1.05] sm:text-[52px]">
            Прозрачный путь <span className="italic">от выбора до практики</span>
          </h2>
        </FadeIn>
        <div className="mt-12 grid gap-4 md:grid-cols-4">
          {steps.map((s, i) => (
            <FadeIn key={s.n} delay={i * 0.05}>
              <div className="h-full rounded-[28px] border border-ink/6 bg-white/70 p-6">
                <p className="font-display text-[28px] text-rose">{s.n}</p>
                <h3 className="mt-4 font-display text-[24px] leading-tight">{s.title}</h3>
                <p className="mt-3 text-sm leading-relaxed text-stone">{s.text}</p>
              </div>
            </FadeIn>
          ))}
        </div>
        <p className="mt-8 max-w-2xl text-sm text-muted">
          Видео нельзя скачать архивом. Доступ защищён и открывается после оплаты. Материалы смотрятся в личном кабинете, PDF можно сохранить на устройство.
        </p>
      </Section>

      <Section className="bg-[#F3EBE3]/50">
        <FadeIn>
          <Eyebrow>Отзывы</Eyebrow>
          <h2 className="font-display text-[40px] leading-[1.05] sm:text-[52px]">
            Тихие <span className="italic">впечатления</span>
          </h2>
        </FadeIn>
        {loading ? (
          <div className="mt-12 grid gap-5 md:grid-cols-2">
            <Skeleton className="h-56" />
            <Skeleton className="h-56" />
          </div>
        ) : (
          <div className="mt-12 grid gap-5 md:grid-cols-2">
            {reviews.map((r, i) => (
              <FadeIn key={r.id} delay={i * 0.05}>
                <blockquote className="h-full rounded-[28px] bg-white p-7 shadow-[0_16px_40px_-30px_rgba(58,49,44,0.4)]">
                  <p className="font-display text-[24px] leading-snug italic">«{r.quote}»</p>
                  <p className="mt-5 text-sm text-stone">{r.result_note}</p>
                  <footer className="mt-6 text-[13px] text-muted">
                    {r.author_name}, {r.author_age} · {r.city}
                    <span className="mx-2">·</span>
                    {r.program_title}
                  </footer>
                </blockquote>
              </FadeIn>
            ))}
          </div>
        )}
      </Section>

      <Section>
        <div className="grid gap-10 lg:grid-cols-[0.8fr_1.2fr]">
          <div>
            <Eyebrow>FAQ</Eyebrow>
            <h2 className="font-display text-[40px] leading-[1.05] sm:text-[52px]">
              Коротко о <span className="italic">главном</span>
            </h2>
          </div>
          <div className="divide-y divide-ink/8 border-y border-ink/8">
            {faqs.map((f) => (
              <div key={f.id}>
                <button
                  className="flex w-full items-center justify-between gap-4 py-5 text-left"
                  onClick={() => setOpenFaq((v) => (v === f.id ? null : f.id))}
                >
                  <span className="font-display text-[22px] leading-tight">{f.question}</span>
                  <ChevronDown size={18} className={`shrink-0 transition ${openFaq === f.id ? 'rotate-180' : ''}`} />
                </button>
                {openFaq === f.id && <p className="pb-5 text-sm leading-relaxed text-stone">{f.answer}</p>}
              </div>
            ))}
          </div>
        </div>
      </Section>

      <Section className="pb-24">
        <div className="overflow-hidden rounded-[36px] bg-ink px-8 py-16 text-center text-cream md:px-16">
          <p className="text-[11px] uppercase tracking-[0.28em] text-blush">Мягкий старт</p>
          <h2 className="mx-auto mt-5 max-w-xl font-display text-[42px] leading-[1.05] sm:text-[58px]">
            Начни с заботы о себе уже сегодня
          </h2>
          <p className="mx-auto mt-5 max-w-md text-sm leading-relaxed text-cream/70">
            Выбери программу в своём темпе. Без давления, без громких обещаний — только ясный путь к телу, в котором спокойно.
          </p>
          <div className="mt-8 flex justify-center">
            <Link
              to="/#programs"
              className="inline-flex rounded-full bg-cream px-8 py-3.5 text-[13px] font-medium text-ink transition hover:bg-white"
            >
              Выбрать программу
            </Link>
          </div>
        </div>
      </Section>
    </div>
  );
}
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

// Внутри компонента Home:
const [latestPosts, setLatestPosts] = useState([]);

useEffect(() => {
  fetch('/api/posts')
    .then(res => res.json())
    .then(data => setLatestPosts(data.slice(0, 3)));
}, []);

// В JSX, перед Footer:
{latestPosts.length > 0 && (
  <section className="py-16 bg-white">
    <div className="container mx-auto px-4">
      <h2 className="text-3xl font-bold text-center mb-12">
        Последние статьи
      </h2>
      <div className="grid md:grid-cols-3 gap-8">
        {latestPosts.map(post => (
          <Link
            key={post.id}
            to={`/blog/${post.slug}`}
            className="group bg-white rounded-xl shadow hover:shadow-lg transition-all"
          >
            {post.cover_image && (
              <img
                src={post.cover_image}
                alt={post.title}
                className="w-full h-48 object-cover rounded-t-xl"
              />
            )}
            <div className="p-6">
              <h3 className="text-lg font-bold mb-2 group-hover:text-pink-600">
                {post.title}
              </h3>
              {post.excerpt && (
                <p className="text-gray-600 text-sm line-clamp-2">
                  {post.excerpt}
                </p>
              )}
            </div>
          </Link>
        ))}
      </div>
      <div className="text-center mt-8">
        <Link
          to="/blog"
          className="inline-block px-6 py-3 bg-pink-600 hover:bg-pink-700 text-white font-semibold rounded-lg transition-colors"
        >
          Все статьи →
        </Link>
      </div>
    </div>
  </section>
)}

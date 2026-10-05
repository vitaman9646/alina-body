import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, ChevronDown, Flower2, Heart, Sparkles, Wind } from 'lucide-react';
import { ButtonLink, Eyebrow, FadeIn, Section, Skeleton } from '../components/ui';
import BeforeAfter from '../components/BeforeAfter';
import { api, type Faq, type Review } from '../lib/api';

type Post = {
  id: number;
  title: string;
  slug: string;
  excerpt: string;
  cover_image: string;
  published_at: string;
};

const pains = [
  { title: 'Нет времени на зал', text: '20–30 минут дома. Без дороги, без очереди к тренажёрам, без чужого ритма.' },
  { title: 'Страх начать «не идеально»', text: 'Программы собраны так, чтобы можно было войти мягко — даже если давно не двигались.' },
  { title: 'Жёсткие ограничения утомляют', text: 'Никакой гонки и наказаний. Только устойчивый ритм, который можно удержать.' },
  { title: 'Результат не держится', text: 'Мы работаем с осанкой, дыханием и привычкой — чтобы тело оставалось собранным после курса.' },
];

const results = [
  { title: 'Лёгкость и энергия', text: 'Тело перестаёт казаться тяжёлым. Появляется ровное утро и спокойный тонус дня.', icon: Wind },
  { title: 'Подтянутый тонус', text: 'Мягкая плотность мышц, собранный кор и более ясный силуэт — без изнурения.', icon: Sparkles },
  { title: 'Уверенность в себе', text: 'Когда осанка выравнивается, меняется и ощущение себя. Это видно в зеркале и в походке.', icon: Heart },
  { title: 'Здоровая привычка', text: 'Короткие занятия, которые встраиваются в жизнь. Не подвиг, а ежедневная забота.', icon: Flower2 },
];

const steps = [
  { n: '01', title: 'Выбор мини-курса', text: 'Короткие программы под свою цель: 3–7 дней, 15–20 минут в день. Спокойно выберите зону тела.' },
  { n: '02', title: 'Безопасная оплата', text: 'Оплата проходит через ЮKassa. Карта, СБП и привычные способы — без лишних шагов.' },
  { n: '03', title: 'Мгновенный доступ', text: 'Сразу после оплаты открывается личный кабинет. Уроки и PDF уже на месте.' },
  { n: '04', title: 'Онлайн-просмотр', text: 'Видео смотрятся только в кабинете. Скачать архив нельзя — так мы бережём материалы. PDF можно сохранить себе.' },
];

// Истории трансформаций (фото «до/после») — заполняются после генерации в kie.ai
const cases: { name: string; before: string; after: string }[] = [];

export default function Home() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [faqs, setFaqs] = useState<Faq[]>([]);
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  const load = async () => {
    setLoading(true);
    try {
      const [r, f] = await Promise.all([
        api<Review[]>('/api/content?type=reviews'),
        api<Faq[]>('/api/content?type=faqs'),
      ]);
      setReviews(r);
      setFaqs(f);
    } catch {
      // тихо — секции останутся пустыми, если контент не загрузился
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    api<Post[]>('/api/posts')
      .then(setPosts)
      .catch(() => setPosts([]));
  }, []);

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
              Короткие домашние мини-курсы для тонуса, осанки и лёгкой энергии — без жёстких ограничений.
            </p>
            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <ButtonLink to="/tonus-doma">Выбрать мини-курс</ButtonLink>
              <ButtonLink to="/#about" variant="ghost">Об Алине</ButtonLink>
            </div>
            <p className="mt-8 text-[13px] tracking-wide text-muted">
              Методики реальных тренеров · мягкая сила без изнурения
            </p>
          </FadeIn>

          <FadeIn delay={0.12} className="relative">
            <div className="relative mx-auto max-w-[480px]">
              <div className="absolute -left-6 top-10 hidden h-28 w-28 rounded-full bg-blush/70 blur-2xl sm:block" />
              <div className="absolute -right-4 bottom-16 hidden h-24 w-24 rounded-full bg-sand/80 blur-2xl sm:block" />
              <img
                src="/images/hero-alina.jpg"
                alt="Алина — тренер Alina Body"
                className="relative z-10 aspect-[3/4] w-full rounded-[36px] object-cover shadow-[0_30px_80px_-28px_rgba(92,64,56,0.35)]"
              />
            </div>
          </FadeIn>
        </div>
      </section>

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
        <div className="grid items-center gap-10 overflow-hidden rounded-[36px] bg-white shadow-[0_20px_50px_-32px_rgba(58,49,44,0.4)] md:grid-cols-2">
          <div className="px-7 py-10 md:px-12 md:py-14">
            <Eyebrow>Мини-курсы</Eyebrow>
            <h2 className="font-display text-[40px] leading-[1.05] sm:text-[52px]">
              Короткие программы <span className="italic">под свою цель</span>
            </h2>
            <p className="mt-5 max-w-md text-[15px] leading-relaxed text-stone">
              3–7 дней, 15–20 минут в день. Выберите зону тела или цель — и начните с малого шага, без давления.
            </p>
            <div className="mt-8">
              <ButtonLink to="/tonus-doma">
                Смотреть мини-курсы <ArrowRight size={15} className="ml-2" />
              </ButtonLink>
            </div>
          </div>
          <img
            src="/images/hero-alina.jpg"
            alt="Мини-курсы Alina Body"
            className="h-full min-h-[320px] w-full object-cover md:min-h-[440px]"
          />
        </div>
      </Section>

      <Section id="about">
        <div className="grid items-center gap-12 lg:grid-cols-[0.9fr_1.1fr]">
          <FadeIn>
            <div className="relative mx-auto max-w-md">
              <img
                src="/images/hero-alina.jpg"
                alt="Алина — тренер Alina Body"
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
              Алина — ваш проводник в домашний фитнес. Её программы собраны по методикам
              реальных тренеров и проверенным источникам: без магии, без «волшебных таблеток»
              и обещаний «новой жизни за неделю».
            </p>
            <p className="mt-4 max-w-xl text-[15px] leading-relaxed text-stone">
              В основе подхода — осанка, дыхание, глубокий кор, суставы и устойчивый результат.
              Сила здесь тихая. Она собирает тело изнутри и оставляет ощущение лёгкости.
            </p>
            <div className="mt-8 grid grid-cols-3 gap-3">
              {[
                ['24/7', 'рядом с тобой'],
                ['100+', 'проверенных источников'],
                ['0', 'осуждения и давления'],
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
              <article className="h-full rounded-[28px] bg-white p-7 shadow-[0_16px_40px_-30px_rgba(58,49,44,0.4)]">
                <r.icon size={18} className="text-rose" />
                <h3 className="mt-3 font-display text-[28px]">{r.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-stone">{r.text}</p>
              </article>
            </FadeIn>
          ))}
        </div>
      </Section>

      <Section>
        <FadeIn>
          <Eyebrow>Истории результатов</Eyebrow>
          <h2 className="max-w-lg font-display text-[40px] leading-[1.05] sm:text-[52px]">
            До и <span className="italic">после</span>
          </h2>
        </FadeIn>
        {cases.length > 0 ? (
          <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {cases.map((c) => (
              <div key={c.name}>
                <BeforeAfter before={c.before} after={c.after} />
                <p className="mt-3 text-center text-sm text-stone">{c.name}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="mt-12 rounded-[32px] border border-dashed border-rose/40 bg-white/60 px-8 py-16 text-center">
            <p className="font-display text-[26px] italic text-stone">Первые истории результатов скоро появятся</p>
            <p className="mx-auto mt-3 max-w-md text-sm text-muted">
              Трансформации наших учениц — с фото до и после.
            </p>
          </div>
        )}
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

      {posts.length > 0 && (
        <Section className="bg-[#F3EBE3]/50">
          <FadeIn>
            <Eyebrow>Блог</Eyebrow>
            <h2 className="font-display text-[40px] leading-[1.05] sm:text-[52px]">
              Последние <span className="italic">статьи</span>
            </h2>
          </FadeIn>
          <div className="mt-12 grid gap-5 md:grid-cols-3">
            {posts.map((post, i) => (
              <FadeIn key={post.id} delay={i * 0.05}>
                <Link
                  to={`/blog/${post.slug}`}
                  className="group block h-full overflow-hidden rounded-[28px] bg-white shadow-[0_16px_40px_-30px_rgba(58,49,44,0.4)]"
                >
                  {post.cover_image && (
                    <div className="h-48 overflow-hidden">
                      <img
                        src={post.cover_image}
                        alt={post.title}
                        className="h-full w-full object-cover transition duration-500 group-hover:scale-105"
                      />
                    </div>
                  )}
                  <div className="p-6">
                    <h3 className="font-display text-[24px] leading-tight transition group-hover:text-rose">
                      {post.title}
                    </h3>
                    {post.excerpt && (
                      <p className="mt-3 text-sm leading-relaxed text-stone line-clamp-3">{post.excerpt}</p>
                    )}
                    <p className="mt-4 text-[12px] uppercase tracking-[0.18em] text-muted">
                      {new Date(post.published_at).toLocaleDateString('ru-RU')} · читать
                    </p>
                  </div>
                </Link>
              </FadeIn>
            ))}
          </div>
          <div className="mt-10 text-center">
            <ButtonLink to="/blog" variant="ghost">
              Все статьи <ArrowRight size={15} className="ml-2" />
            </ButtonLink>
          </div>
        </Section>
      )}

      <Section className="pb-24">
        <div className="overflow-hidden rounded-[36px] bg-ink px-8 py-16 text-center text-cream md:px-16">
          <p className="text-[11px] uppercase tracking-[0.28em] text-blush">Мягкий старт</p>
          <h2 className="mx-auto mt-5 max-w-xl font-display text-[42px] leading-[1.05] sm:text-[58px]">
            Начни с заботы о себе уже сегодня
          </h2>
          <p className="mx-auto mt-5 max-w-md text-sm leading-relaxed text-cream/70">
            Выберите мини-курс в своём темпе. Без давления, без громких обещаний — только ясный путь к телу, в котором спокойно.
          </p>
          <div className="mt-8 flex justify-center">
            <Link
              to="/tonus-doma"
              className="inline-flex rounded-full bg-cream px-8 py-3.5 text-[13px] font-medium text-ink transition hover:bg-white"
            >
              Выбрать мини-курс
            </Link>
          </div>
        </div>
      </Section>
    </div>
  );
}

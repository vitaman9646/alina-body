import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Check, ChevronDown, Flower2, Heart, Sparkles, Wind } from 'lucide-react';
import { ButtonLink, ErrorNote, Eyebrow, FadeIn, Section, Skeleton } from '../components/ui';
import { api, formatPrice, type Faq, type Program, type Review } from '../lib/api';

type Post = {
  id: number;
  title: string;
  slug: string;
  excerpt: string;
  cover_image: string;
  published_at: string;
};

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
  const [posts, setPosts] = useState<Post[]>([]);
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

  useEffect(() => {
    api<Post[]>('/api/posts')
      .then(setPosts)
      .catch(() => setPosts([]));
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
              ИИ-модель · методики реальных тренеров · мягкая сила без изнурения
            </p>
          </FadeIn>

          <FadeIn delay={0.12} className="relative">
            <div className="relative mx-auto max-w-[480px]">
              <div className="absolute -left-6 top-10 hidden h-28 w-28 rounded-full bg-blush/70 blur-2xl sm:block" />
              <div className="absolute -right-4 bottom-16 hidden h-24 w-24 rounded-full bg-sand/80 blur-2xl sm:block" />
              <img
                src="/images/hero-alina.jpg"
                alt="Алина — ИИ фитнес-модель Alina Body"
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

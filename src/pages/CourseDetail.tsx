import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Check } from 'lucide-react';
import { ErrorNote, Eyebrow, FadeIn, Section, Skeleton } from '../components/ui';
import { api, formatPrice } from '../lib/api';
import Seo from '../components/Seo';

type LessonItem = {
  title: string;
  description: string;
  image: string | null;
  duration_min: number | null;
};

type ModuleItem = {
  title: string;
  description: string;
  lessons: LessonItem[];
};

type Course = {
  slug: string;
  title: string;
  description: string;
  price: number;
  currency: string;
  duration_days: number;
  level: string;
  cover_url: string | null;
  modules: ModuleItem[];
};

export default function CourseDetail() {
  const { slug } = useParams();
  const [course, setCourse] = useState<Course | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api<Course>(`/api/mini-course-themes?slug=${slug}`);
      setCourse(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось загрузить программу');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [slug]);

  if (loading) {
    return (
      <Section>
        <Skeleton className="h-96" />
      </Section>
    );
  }

  if (error || !course) {
    return (
      <Section>
        <ErrorNote message={error || 'Программа не найдена'} onRetry={load} />
      </Section>
    );
  }

  const totalLessons = course.modules.reduce((n, m) => n + m.lessons.length, 0);

  return (
    <div>
      <Seo
        title={`${course.title} — Alina Body`}
        description={course.description}
        path={`/tonus-doma/${course.slug}`}
      />

      <Section className="pt-16 pb-8">
        <FadeIn>
          <Link to="/tonus-doma" className="inline-flex items-center gap-2 text-[13px] text-stone hover:text-ink">
            <ArrowLeft size={14} /> Все мини-курсы
          </Link>

          <div className="mt-8">
            <Eyebrow>Мини-курс · {course.duration_days} дней</Eyebrow>
          </div>
          <h1 className="mt-3 max-w-2xl font-display text-[40px] leading-[1.05] sm:text-[54px]">
            {course.title}
          </h1>
          <p className="mt-5 max-w-xl text-[16px] leading-relaxed text-stone">{course.description}</p>

          <div className="mt-7 flex flex-wrap items-center gap-4">
            <p className="font-display text-[32px]">{formatPrice(course.price)}</p>
            <span className="text-sm text-stone">· {course.duration_days} дней · дома, без зала</span>
          </div>

          <Link
            to="/checkout"
            className="mt-7 inline-flex items-center gap-2 rounded-full bg-ink px-8 py-4 text-[14px] font-medium text-cream transition-colors hover:bg-[#2b241f]"
          >
            Начать программу <ArrowRight size={16} />
          </Link>
        </FadeIn>
      </Section>

      <Section className="pt-0">
        <div className="grid gap-6">
          {course.modules.map((m, i) => (
            <FadeIn key={i} delay={i * 0.04}>
              <div className="overflow-hidden rounded-[32px] border border-ink/6 bg-white/60">
                <div className="px-6 pt-6 md:px-9 md:pt-8">
                  <h2 className="font-display text-[26px] leading-tight">{m.title}</h2>
                  {m.description && <p className="mt-1.5 text-sm text-stone">{m.description}</p>}
                </div>
                <ul className="mt-5 divide-y divide-ink/5">
                  {m.lessons.map((l, j) => (
                    <li key={j} className="flex items-start gap-5 px-6 py-5 md:px-9">
                      {l.image ? (
                        <img
                          src={l.image}
                          alt={l.title}
                          loading="lazy"
                          className="h-20 w-16 shrink-0 rounded-xl object-cover"
                        />
                      ) : (
                        <div className="h-20 w-16 shrink-0 rounded-xl bg-sand" />
                      )}
                      <div className="min-w-0">
                        <p className="font-medium text-ink">{l.title}</p>
                        {l.description && (
                          <p className="mt-1 text-sm leading-relaxed text-stone">{l.description}</p>
                        )}
                        {l.duration_min != null && (
                          <p className="mt-1 text-xs text-muted">~{l.duration_min} мин</p>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            </FadeIn>
          ))}
        </div>
      </Section>

      <Section className="bg-[#F3EBE3]/50">
        <div className="mx-auto max-w-lg text-center">
          <Eyebrow>{totalLessons} занятий · {course.duration_days} дней</Eyebrow>
          <h2 className="mt-3 font-display text-[30px] leading-tight">Начните с малого шага</h2>
          <p className="mt-3 text-sm leading-relaxed text-stone">
            {course.duration_days} дней по 15–20 минут дома. Мягкая подача, без зала и железа.
          </p>
          <Link
            to="/checkout"
            className="mt-7 inline-flex items-center gap-2 rounded-full bg-ink px-8 py-4 text-[14px] font-medium text-cream transition-colors hover:bg-[#2b241f]"
          >
            Начать программу <ArrowRight size={16} />
          </Link>
        </div>
      </Section>
    </div>
  );
}

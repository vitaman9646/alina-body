import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Check } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../lib/api';

interface Lesson {
  title: string;
  description: string;
  image: string | null;
  duration_min: number | null;
}
interface Module {
  title: string;
  description: string;
  lessons: Lesson[];
}
interface Course {
  id: string;
  slug: string;
  title: string;
  description: string;
  price: number;
  currency: string;
  duration_days: number;
  level: string;
  cover_url: string | null;
  modules: Module[];
}

export default function CourseLanding() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const { user, token } = useAuth();
  const [course, setCourse] = useState<Course | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [payError, setPayError] = useState('');

  const buy = async () => {
    if (!course) return;
    setPayError('');
    if (!user) {
      navigate(`/auth?next=${encodeURIComponent(`/course/${course.slug}`)}`, { replace: true });
      return;
    }
    setBusy(true);
    try {
      const res = await api<{ payment_url?: string; alreadyEnrolled?: boolean }>('/api/checkout', {
        method: 'POST',
        token,
        body: JSON.stringify({ program_id: course.id }),
      });
      if (res.alreadyEnrolled) {
        navigate(`/learn/${course.slug}`, { replace: true });
      } else if (res.payment_url) {
        window.location.href = res.payment_url;
      } else {
        setPayError('Не удалось создать платёж, попробуйте ещё раз.');
      }
    } catch (e) {
      setPayError(e instanceof Error ? e.message : 'Не удалось создать платёж');
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    fetch(`/api/mini-course-themes?slug=${encodeURIComponent(slug || '')}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error('курс не найден'))))
      .then((d) => setCourse(d))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center bg-milk"><div className="h-10 w-10 animate-spin rounded-full border-2 border-ink/15 border-t-ink" /></div>;
  }
  if (error || !course) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-milk px-5 text-center">
        <div>
          <h1 className="font-display text-2xl text-ink mb-4">Курс не найден</h1>
          <Link to="/" className="text-rose hover:underline">← На главную</Link>
        </div>
      </div>
    );
  }

  const lessonCount = course.modules.reduce((n, m) => n + m.lessons.length, 0);
  const totalImages = course.modules.flatMap((m) => m.lessons.map((l) => l.image)).filter(Boolean);

  return (
    <div className="min-h-screen bg-milk text-ink">
      {/* Hero */}
      <section className="px-5 pt-12 pb-10 sm:px-8">
        <div className="mx-auto max-w-3xl">
          <Link to="/" className="inline-flex items-center gap-2 text-sm text-muted hover:text-rose mb-8">
            <ArrowLeft className="w-4 h-4" /> На главную
          </Link>
          {course.cover_url && (
            <div className="mb-8 overflow-hidden rounded-2xl">
              <img src={course.cover_url} alt={course.title} className="w-full h-64 sm:h-80 object-cover" />
            </div>
          )}
          <h1 className="font-display text-3xl sm:text-5xl leading-tight mb-4">{course.title}</h1>
          <p className="text-lg text-muted leading-relaxed mb-6">{course.description}</p>

          <div className="flex flex-wrap items-center gap-4 mb-8">
            <div className="font-display text-4xl text-rose">
              {course.price.toLocaleString('ru-RU')} ₽
            </div>
            <div className="text-sm text-muted leading-tight">
              <div>единоразово · доступ навсегда</div>
              <div>{course.modules.length} модулей · {lessonCount} уроков</div>
            </div>
          </div>

          <button
            onClick={buy}
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-full bg-ink px-8 py-4 text-[15px] font-medium text-cream transition hover:bg-[#2b241f] disabled:opacity-60"
          >
            {busy ? 'Создаём платёж…' : `Купить за ${course.price.toLocaleString('ru-RU')} ₽`}
          </button>
          <p className="mt-3 text-xs text-muted">Оплата картой или СБП, доступ открывается сразу после оплаты.</p>
          {payError && <p className="mt-3 text-sm text-[#9a4b43]">{payError}</p>}
        </div>
      </section>

      {/* Что внутри */}
      <section className="px-5 py-12 sm:px-8 bg-[#F3EBE3]">
        <div className="mx-auto max-w-3xl">
          <h2 className="font-display text-2xl sm:text-3xl mb-8">Что внутри курса</h2>
          <div className="space-y-6">
            {course.modules.map((m, i) => (
              <div key={i} className="rounded-2xl bg-milk p-6">
                <div className="text-xs uppercase tracking-[0.2em] text-rose mb-1">Модуль {i + 1}</div>
                <h3 className="font-display text-xl mb-1">{m.title}</h3>
                <p className="text-sm text-muted mb-4">{m.lessons.length} уроков</p>
                <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
                  {m.lessons.slice(0, 8).map((l, j) => (
                    <div key={j} className="overflow-hidden rounded-lg" title={l.title}>
                      {l.image ? (
                        <img src={l.image} alt={l.title} loading="lazy" className="aspect-square w-full object-cover" />
                      ) : (
                        <div className="aspect-square w-full bg-blush flex items-center justify-center text-[10px] text-muted text-center px-1">
                          {l.title}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Финал */}
      <section className="px-5 py-14 sm:px-8">
        <div className="mx-auto max-w-3xl rounded-2xl border border-rose/30 bg-blush/40 p-8 text-center">
          <h2 className="font-display text-2xl sm:text-3xl mb-3">Сытно, полезно и без переплат</h2>
          <p className="text-muted mb-6">
            {course.modules.length} модулей · {lessonCount} уроков с граммовками, КБЖУ и себестоимостью — всё в одном курсе.
          </p>
          <button
            onClick={buy}
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-full bg-rose px-8 py-4 text-[15px] font-semibold text-white transition hover:bg-[#c76a60] disabled:opacity-60"
          >
            <Check className="w-5 h-5" /> {busy ? 'Создаём платёж…' : `Купить за ${course.price.toLocaleString('ru-RU')} ₽`}
          </button>
        </div>
      </section>
    </div>
  );
}

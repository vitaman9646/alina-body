import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Check, CheckCircle2, List } from 'lucide-react';
import { Button, ErrorNote, Skeleton } from '../components/ui';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../lib/api';

interface ViewerLesson {
  id: string;
  title: string;
  description: string;
  lesson_type: string;
  duration_minutes: number | null;
  is_preview: boolean;
  locked: boolean;
  file_url: string | null;
  video_url: string | null;
  content: string | null;
  sort_order: number;
}
interface ViewerModule {
  id: string;
  title: string;
  description: string;
  lessons: ViewerLesson[];
}
interface ViewerData {
  course: {
    id: string;
    slug: string;
    title: string;
    description: string;
    cover_url: string | null;
    price: number;
    currency: string;
  };
  access: 'paid' | 'none';
  modules: ViewerModule[];
  progress: Record<string, boolean>;
}

export default function Learn() {
  const { slug } = useParams<{ slug: string }>();
  const { token } = useAuth();
  const [data, setData] = useState<ViewerData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeId, setActiveId] = useState<string | null>(null);
  const [done, setDone] = useState<Record<string, boolean>>({});
  const [saving, setSaving] = useState(false);
  const [navOpen, setNavOpen] = useState(false);
  const autoRetried = useRef(false);

  const flatLessons = useMemo(
    () => (data ? data.modules.flatMap((m) => m.lessons) : []),
    [data]
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const d = await api<ViewerData>(`/api/course-viewer?slug=${encodeURIComponent(slug || '')}`, { token });
      setData(d);
      setDone(d.progress || {});
      const first = d.modules.flatMap((m) => m.lessons)[0];
      setActiveId((prev) => prev ?? first?.id ?? null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось открыть курс');
    } finally {
      setLoading(false);
    }
  }, [slug, token]);

  useEffect(() => {
    load();
  }, [load]);

  // После оплаты вебхук может подтвердить покупку чуть позже редиректа на /learn —
  // при «нет доступа» один раз автоматически перечитываем курс.
  useEffect(() => {
    if (data?.access !== 'none' || error || autoRetried.current) return;
    autoRetried.current = true;
    const t = setTimeout(() => load(), 4000);
    return () => clearTimeout(t);
  }, [data?.access, error, load]);

  const active = useMemo(
    () => flatLessons.find((l) => l.id === activeId) || flatLessons[0] || null,
    [flatLessons, activeId]
  );
  const activeIndex = active ? flatLessons.findIndex((l) => l.id === active.id) : -1;

  const completedCount = flatLessons.filter((l) => done[l.id]).length;
  const percent = flatLessons.length ? Math.round((completedCount / flatLessons.length) * 100) : 0;

  const markDone = async () => {
    if (!active || done[active.id]) return;
    setSaving(true);
    try {
      await api('/api/progress', {
        method: 'POST',
        token,
        body: JSON.stringify({ lesson_id: active.id, completed: true }),
      });
      setDone((prev) => ({ ...prev, [active.id]: true }));
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось отметить урок');
    } finally {
      setSaving(false);
    }
  };

  const goTo = (dir: 1 | -1) => {
    const next = flatLessons[activeIndex + dir];
    if (next) setActiveId(next.id);
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-milk px-5">
        <Skeleton className="h-[70vh] w-full max-w-6xl" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex min-h-screen justify-center bg-milk px-5 py-16">
        <div className="w-full max-w-3xl">
          <ErrorNote message={error || 'Курс не найден'} onRetry={load} />
        </div>
      </div>
    );
  }

  // Нет доступа → предложение купить
  if (data.access !== 'paid') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-milk px-5">
        <div className="w-full max-w-lg rounded-[32px] bg-white p-10 text-center shadow-[0_16px_50px_-30px_rgba(58,49,44,0.4)]">
          <p className="text-[11px] uppercase tracking-[0.28em] text-rose">Курс</p>
          <h1 className="mt-2 font-display text-[38px] leading-tight">{data.course.title}</h1>
          <p className="mt-4 text-sm text-stone">
            Уроки этого курса откроются после оплаты. Оплата картой или СБП, доступ — сразу.
          </p>
          <div className="mt-8 space-y-3">
            <ButtonLinkWrap to={`/course/${data.course.slug}`}>
              Купить за {data.course.price.toLocaleString('ru-RU')} ₽
            </ButtonLinkWrap>
            <button
              onClick={() => {
                autoRetried.current = false;
                load();
              }}
              className="block w-full text-[13px] text-muted underline underline-offset-4"
            >
              Я уже оплатил — проверить доступ
            </button>
            <Link to="/dashboard" className="block text-[13px] text-muted underline underline-offset-4">
              ← Мои курсы
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const isDone = active ? !!done[active.id] : false;

  return (
    <div className="min-h-screen bg-milk">
      <div className="mx-auto max-w-6xl px-5 py-8">
        <div className="flex items-center justify-between gap-3">
          <Link to="/dashboard" className="inline-flex items-center gap-2 text-[13px] text-muted hover:text-rose">
            <ArrowLeft size={14} /> Мои курсы
          </Link>
          <button
            onClick={() => setNavOpen((v) => !v)}
            className="inline-flex items-center gap-2 rounded-full border border-ink/10 bg-white px-4 py-2 text-[13px] lg:hidden"
          >
            <List size={15} /> Содержание
          </button>
        </div>

        <div className="mt-4 grid gap-6 lg:grid-cols-[340px_1fr] lg:items-start">
          {/* Сайдбар: модули и уроки */}
          <aside className={`${navOpen ? 'block' : 'hidden'} lg:block`}>
            <div className="rounded-[28px] bg-white p-6 lg:sticky lg:top-24">
              <h1 className="font-display text-[26px] leading-tight">{data.course.title}</h1>
              <div className="mt-3 flex items-center gap-3">
                <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-cream">
                  <div className="h-full rounded-full bg-rose" style={{ width: `${percent}%` }} />
                </div>
                <span className="text-xs text-muted">{percent}%</span>
              </div>
              <p className="mt-1 text-xs text-muted">
                {completedCount} из {flatLessons.length} уроков
              </p>

              <div className="mt-6 space-y-5">
                {data.modules.map((m, mi) => (
                  <div key={m.id}>
                    <p className="text-[11px] uppercase tracking-[0.18em] text-rose">
                      {mi + 1}. {m.title}
                    </p>
                    <div className="mt-2 space-y-1">
                      {m.lessons.map((l) => {
                        const activeHere = active?.id === l.id;
                        const completedHere = !!done[l.id];
                        return (
                          <button
                            key={l.id}
                            onClick={() => {
                              setActiveId(l.id);
                              setNavOpen(false);
                            }}
                            className={`flex w-full items-start gap-2 rounded-[14px] px-3 py-2 text-left text-sm transition ${
                              activeHere ? 'bg-blush/60' : 'hover:bg-cream'
                            }`}
                          >
                            <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center">
                              {completedHere ? (
                                <CheckCircle2 size={15} className="text-moss" />
                              ) : (
                                <span className="h-1.5 w-1.5 rounded-full bg-sand" />
                              )}
                            </span>
                            <span className={completedHere ? 'text-muted' : ''}>{l.title}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </aside>

          {/* Контент урока */}
          <main className="min-w-0">
            {active ? (
              <div className="rounded-[28px] bg-white p-6 md:p-10">
                <p className="text-[11px] uppercase tracking-[0.22em] text-rose">
                  Урок {activeIndex + 1} из {flatLessons.length}
                  {active.duration_minutes ? ` · ${active.duration_minutes} мин` : ''}
                </p>
                <h2 className="mt-2 font-display text-[34px] leading-tight sm:text-[42px]">{active.title}</h2>
                {active.description && (
                  <p className="mt-3 text-sm leading-relaxed text-stone">{active.description}</p>
                )}

                {active.file_url && (
                  <div className="mt-6 overflow-hidden rounded-[20px]">
                    <img src={active.file_url} alt={active.title} className="w-full object-cover" />
                  </div>
                )}

                {active.video_url && (
                  <div className="mt-6 overflow-hidden rounded-[20px] bg-ink">
                    <video
                      className="aspect-video w-full"
                      controls
                      controlsList="nodownload"
                      disablePictureInPicture
                      onContextMenu={(e) => e.preventDefault()}
                      src={active.video_url}
                    />
                  </div>
                )}

                {active.content && (
                  <div
                    className="lesson-body mt-6 space-y-3 text-[15px] leading-relaxed"
                    dangerouslySetInnerHTML={{ __html: active.content }}
                  />
                )}

                <div className="mt-8 flex flex-wrap items-center justify-between gap-4 border-t border-ink/10 pt-6">
                  <button
                    onClick={() => goTo(-1)}
                    disabled={activeIndex <= 0}
                    className="inline-flex items-center gap-2 text-[13px] text-muted disabled:opacity-40"
                  >
                    <ArrowLeft size={14} /> Предыдущий
                  </button>
                  <Button onClick={markDone} disabled={saving || isDone} variant="soft">
                    {isDone ? (
                      <>
                        <Check size={15} /> Урок пройден
                      </>
                    ) : saving ? (
                      'Сохраняем…'
                    ) : (
                      'Отметить как пройденный'
                    )}
                  </Button>
                  <button
                    onClick={() => goTo(1)}
                    disabled={activeIndex >= flatLessons.length - 1}
                    className="inline-flex items-center gap-2 text-[13px] text-muted disabled:opacity-40"
                  >
                    Следующий <ArrowRight size={14} />
                  </button>
                </div>
              </div>
            ) : (
              <div className="rounded-[28px] bg-white p-10 text-center text-sm text-stone">
                В этом курсе пока нет уроков.
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}

// Небольшая обёртка-ссылка в стиле кнопки (Button — это <button>, здесь нужен <Link>).
function ButtonLinkWrap({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <Link
      to={to}
      className="inline-flex items-center justify-center rounded-full bg-ink px-7 py-3.5 text-[13px] font-medium tracking-[0.02em] text-cream transition-all duration-300 hover:bg-[#2b241f]"
    >
      {children}
    </Link>
  );
}

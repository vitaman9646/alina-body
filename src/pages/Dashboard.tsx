import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Download, Lock, Play } from 'lucide-react';
import { Button, ErrorNote, Eyebrow, Section, Skeleton } from '../components/ui';
import { useAuth } from '../contexts/AuthContext';
import supabase from '../lib/supabase';
import {
  api,
  type Enrollment,
  type Lesson,
  type Material,
  type ProgressRow,
  type TrackerRow,
} from '../lib/api';

const moods = [
  { id: 'light', label: 'Легко' },
  { id: 'calm', label: 'Спокойно' },
  { id: 'tired', label: 'Мягко устала' },
  { id: 'strong', label: 'Собрана' },
];

export default function Dashboard() {
  const { user, token } = useAuth();
  const location = useLocation();
  const notice = (location.state as { notice?: string } | null)?.notice;
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [progress, setProgress] = useState<ProgressRow[]>([]);
  const [tracker, setTracker] = useState<TrackerRow[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dayNumber, setDayNumber] = useState(1);
  const [mood, setMood] = useState('calm');
  const [energy, setEnergy] = useState(3);
  const [note, setNote] = useState('');
  const [saving, setSaving] = useState(false);
  const [trackMsg, setTrackMsg] = useState('');

  const load = async () => {
    if (!token) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const [ens, ls, ms, pr, tr] = await Promise.all([
        api<Enrollment[]>('/api/enrollments', { token }),
        api<Lesson[]>('/api/lessons', { token }),
        api<Material[]>('/api/materials', { token }),
        api<ProgressRow[]>('/api/progress', { token }),
        api<TrackerRow[]>('/api/tracker', { token }),
      ]);
      setEnrollments(ens);
      setLessons(ls);
      setMaterials(ms);
      setProgress(pr);
      setTracker(tr);
      if (!activeId && ens[0]) setActiveId(ens[0].program_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось открыть кабинет');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [token]);

  const active = enrollments.find((e) => e.program_id === activeId) || enrollments[0];
  const programLessons = useMemo(
    () => lessons.filter((l) => l.program_id === active?.program_id),
    [lessons, active]
  );
  const programMaterials = useMemo(
    () => materials.filter((m) => m.program_id === active?.program_id),
    [materials, active]
  );
  const doneIds = useMemo(
    () => new Set(progress.filter((p) => p.completed).map((p) => p.lesson_id)),
    [progress]
  );
  const doneCount = programLessons.filter((l) => doneIds.has(l.id)).length;
  const percent = programLessons.length ? Math.round((doneCount / programLessons.length) * 100) : 0;
  const programTracker = tracker.filter((t) => t.program_id === active?.program_id);

  const saveTracker = async (e: FormEvent) => {
    e.preventDefault();
    if (!active) return;
    setSaving(true);
    setTrackMsg('');
    try {
      await api('/api/tracker', {
        method: 'POST',
        token,
        body: JSON.stringify({
          program_id: active.program_id,
          day_number: dayNumber,
          mood,
          energy,
          note,
        }),
      });
      setTrackMsg('День сохранён');
      const rows = await api<TrackerRow[]>(`/api/tracker?program_id=${active.program_id}`, { token });
      setTracker((prev) => [...prev.filter((t) => t.program_id !== active.program_id), ...rows]);
    } catch (err) {
      setTrackMsg(err instanceof Error ? err.message : 'Не сохранилось');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Section>
        <Skeleton className="h-72" />
      </Section>
    );
  }

  return (
    <Section>
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <Eyebrow>Кабинет</Eyebrow>
          <h1 className="font-display text-[42px] leading-tight sm:text-[54px]">
            Здравствуй{user?.email ? ',' : ''}
            <span className="italic"> {user?.email?.split('@')[0] || ''}</span>
          </h1>
          <p className="mt-2 text-sm text-stone">Видео доступны только онлайн. PDF можно скачать.</p>
        </div>
        <button
          onClick={() => supabase.auth.signOut()}
          className="text-[13px] text-muted underline underline-offset-4"
        >
          Выйти
        </button>
      </div>

      {notice && (
        <div className="mt-6 rounded-[22px] bg-blush/70 px-5 py-4 text-sm">{notice}</div>
      )}
      {error && (
        <div className="mt-6">
          <ErrorNote message={error} onRetry={load} />
        </div>
      )}

      {!enrollments.length ? (
        <div className="mt-12 rounded-[32px] bg-white p-10 text-center">
          <h2 className="font-display text-[34px]">Пока нет открытых программ</h2>
          <p className="mx-auto mt-3 max-w-md text-sm text-stone">
            Выберите челлендж или курс — после оплаты уроки появятся здесь.
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Link to="/challenge" className="rounded-full bg-ink px-6 py-3 text-[13px] text-cream">
              Челлендж
            </Link>
            <Link to="/course" className="rounded-full border border-ink/15 px-6 py-3 text-[13px]">
              Курс
            </Link>
          </div>
        </div>
      ) : (
        <>
          <div className="mt-8 flex flex-wrap gap-2">
            {enrollments.map((e) => (
              <button
                key={e.id}
                onClick={() => setActiveId(e.program_id)}
                className={`rounded-full px-4 py-2 text-[13px] ${
                  active?.id === e.id ? 'bg-ink text-cream' : 'bg-white text-stone'
                }`}
              >
                {e.program?.short_title || e.program?.title}
              </button>
            ))}
          </div>

          {active && (
            <div className="mt-8 grid gap-6 lg:grid-cols-[1.4fr_0.8fr]">
              <div className="rounded-[28px] bg-white p-6 md:p-8">
                <div className="flex flex-wrap items-end justify-between gap-4">
                  <div>
                    <p className="text-[11px] uppercase tracking-[0.2em] text-rose">Текущая программа</p>
                    <h2 className="mt-1 font-display text-[32px] leading-tight">{active.program?.title}</h2>
                    <p className="mt-2 text-sm text-muted">
                      Тариф {active.tariff?.name} · доступ до{' '}
                      {new Date(active.access_until).toLocaleDateString('ru-RU')}
                    </p>
                  </div>
                  <p className="font-display text-[28px]">{percent}%</p>
                </div>
                <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-cream">
                  <div className="h-full rounded-full bg-rose" style={{ width: `${percent}%` }} />
                </div>

                <div className="mt-8 space-y-2">
                  {programLessons.map((lesson) => {
                    const done = doneIds.has(lesson.id);
                    return (
                      <Link
                        key={lesson.id}
                        to={lesson.locked ? '#' : `/dashboard/lesson/${lesson.id}`}
                        className={`flex items-center justify-between rounded-[20px] px-4 py-3 ${
                          lesson.locked ? 'bg-cream/70 text-muted' : 'bg-cream hover:bg-blush/50'
                        }`}
                      >
                        <div>
                          <p className="text-[12px] text-muted">
                            День {lesson.day}
                            {lesson.week ? ` · неделя ${lesson.week}` : ''}
                          </p>
                          <p className="text-sm">{lesson.title}</p>
                        </div>
                        <div className="flex items-center gap-3 text-xs text-muted">
                          <span>{lesson.duration_min} мин</span>
                          {lesson.locked ? <Lock size={15} /> : done ? 'готово' : <Play size={15} />}
                        </div>
                      </Link>
                    );
                  })}
                </div>
              </div>

              <div className="space-y-6">
                <div className="rounded-[28px] bg-white p-6">
                  <h3 className="font-display text-[26px]">Материалы</h3>
                  <div className="mt-4 space-y-3">
                    {programMaterials.map((m) => (
                      <div key={m.id} className="rounded-[18px] bg-cream px-4 py-3">
                        <p className="text-sm">{m.title}</p>
                        <p className="mt-1 text-xs text-muted">{m.description}</p>
                        {m.locked || !m.file_url ? (
                          <p className="mt-2 flex items-center gap-1 text-xs text-muted">
                            <Lock size={12} /> откроется после оплаты
                          </p>
                        ) : (
                          <a
                            href={m.file_url}
                            download
                            className="mt-2 inline-flex items-center gap-1 text-xs underline underline-offset-4"
                          >
                            <Download size={12} /> Скачать PDF
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-[28px] bg-white p-6">
                  <h3 className="font-display text-[26px]">Трекер</h3>
                  <form onSubmit={saveTracker} className="mt-4 space-y-3">
                    <label className="block text-xs text-muted">
                      День
                      <input
                        type="number"
                        min={1}
                        max={60}
                        value={dayNumber}
                        onChange={(e) => setDayNumber(Number(e.target.value))}
                        className="mt-1 w-full rounded-xl border border-ink/10 bg-cream px-3 py-2 text-sm"
                      />
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {moods.map((m) => (
                        <button
                          type="button"
                          key={m.id}
                          onClick={() => setMood(m.id)}
                          className={`rounded-full px-3 py-1.5 text-xs ${
                            mood === m.id ? 'bg-ink text-cream' : 'bg-cream'
                          }`}
                        >
                          {m.label}
                        </button>
                      ))}
                    </div>
                    <label className="block text-xs text-muted">
                      Энергия: {energy}
                      <input
                        type="range"
                        min={1}
                        max={5}
                        value={energy}
                        onChange={(e) => setEnergy(Number(e.target.value))}
                        className="mt-2 w-full"
                      />
                    </label>
                    <textarea
                      value={note}
                      onChange={(e) => setNote(e.target.value)}
                      placeholder="Короткая заметка"
                      className="w-full rounded-xl border border-ink/10 bg-cream px-3 py-2 text-sm"
                      rows={3}
                    />
                    <Button type="submit" disabled={saving} className="w-full">
                      {saving ? 'Сохраняем…' : 'Отметить день'}
                    </Button>
                    {trackMsg && <p className="text-xs text-muted">{trackMsg}</p>}
                  </form>
                  {!!programTracker.length && (
                    <div className="mt-5 space-y-2">
                      {programTracker.slice(-5).reverse().map((t) => (
                        <p key={t.id} className="text-xs text-muted">
                          День {t.day_number} · энергия {t.energy}
                          {t.note ? ` · ${t.note}` : ''}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </Section>
  );
}

import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Lock } from 'lucide-react';
import { Button, ErrorNote, Section, Skeleton } from '../components/ui';
import { useAuth } from '../contexts/AuthContext';
import { api, type Lesson as LessonType } from '../lib/api';

export default function Lesson() {
  const { id } = useParams();
  const { token } = useAuth();
  const [lesson, setLesson] = useState<LessonType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [done, setDone] = useState(false);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api<LessonType>(`/api/lessons?id=${id}`, { token });
      setLesson(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось открыть урок');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [id, token]);

  const mark = async () => {
    if (!lesson) return;
    setSaving(true);
    try {
      await api('/api/progress', {
        method: 'POST',
        token,
        body: JSON.stringify({ lesson_id: lesson.id, completed: true }),
      });
      setDone(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось отметить урок');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Section>
        <Skeleton className="h-[70vh]" />
      </Section>
    );
  }
  if (error || !lesson) {
    return (
      <Section>
        <ErrorNote message={error || 'Урок не найден'} onRetry={load} />
      </Section>
    );
  }

  return (
    <Section>
      <Link to="/dashboard" className="inline-flex items-center gap-2 text-[13px] text-muted">
        <ArrowLeft size={14} /> Назад в кабинет
      </Link>
      <p className="mt-6 text-[11px] uppercase tracking-[0.22em] text-rose">
        День {lesson.day} · {lesson.duration_min} минут
      </p>
      <h1 className="mt-2 font-display text-[40px] leading-tight sm:text-[52px]">{lesson.title}</h1>
      <p className="mt-4 max-w-2xl text-sm leading-relaxed text-stone">{lesson.description}</p>

      <div className="mt-8 overflow-hidden rounded-[28px] bg-ink">
        {lesson.locked || !lesson.video_url ? (
          <div className="flex aspect-video flex-col items-center justify-center gap-3 text-cream">
            <Lock />
            <p className="text-sm text-cream/70">Видео откроется после оплаты программы</p>
            <Link to="/checkout" className="rounded-full bg-cream px-5 py-2 text-[13px] text-ink">
              Открыть доступ
            </Link>
          </div>
        ) : (
          <video
            className="aspect-video w-full"
            controls
            controlsList="nodownload"
            disablePictureInPicture
            onContextMenu={(e) => e.preventDefault()}
            src={lesson.video_url}
          />
        )}
      </div>
      <p className="mt-3 text-xs text-muted">Онлайн-просмотр. Скачивание видео недоступно.</p>

      {!lesson.locked && (
        <div className="mt-8">
          <Button onClick={mark} disabled={saving || done}>
            {done ? 'Урок отмечен' : saving ? 'Сохраняем…' : 'Отметить как пройденный'}
          </Button>
        </div>
      )}
    </Section>
  );
}

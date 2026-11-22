import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { ErrorNote, Eyebrow, Section, Skeleton } from '../components/ui';
import { useAuth } from '../contexts/AuthContext';
import supabase from '../lib/supabase';
import { api, type Enrollment } from '../lib/api';

export default function Dashboard() {
  const { user, token } = useAuth();
  const [enrollments, setEnrollments] = useState<Enrollment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    if (!token) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const data = await api<Enrollment[]>('/api/enrollments', { token });
      setEnrollments(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Не удалось открыть кабинет');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [token]);

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
          <p className="mt-2 text-sm text-stone">Ваши оплаченные курсы.</p>
        </div>
        <button
          onClick={() => supabase.auth.signOut()}
          className="text-[13px] text-muted underline underline-offset-4"
        >
          Выйти
        </button>
      </div>

      {error && (
        <div className="mt-6">
          <ErrorNote message={error} onRetry={load} />
        </div>
      )}

      {!enrollments.length ? (
        <div className="mt-12 rounded-[32px] bg-white p-10 text-center">
          <h2 className="font-display text-[34px]">Пока нет открытых курсов</h2>
          <p className="mx-auto mt-3 max-w-md text-sm text-stone">
            Выберите курс — после оплаты уроки появятся здесь.
          </p>
          <div className="mt-6 flex justify-center">
            <Link to="/courses" className="rounded-full bg-ink px-6 py-3 text-[13px] text-cream">
              Каталог курсов
            </Link>
          </div>
        </div>
      ) : (
        <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {enrollments.map((e) => {
            const course = e.program;
            if (!course) return null;
            return (
              <div key={e.id} className="overflow-hidden rounded-[24px] bg-white">
                {course.image_url ? (
                  <img src={course.image_url} alt={course.title} className="h-40 w-full object-cover" />
                ) : (
                  <div className="h-40 w-full bg-blush" />
                )}
                <div className="p-5">
                  <h3 className="font-display text-[22px] leading-tight">{course.title}</h3>
                  {(course.tagline || course.description) && (
                    <p className="mt-2 line-clamp-3 text-xs text-muted">
                      {course.tagline || course.description}
                    </p>
                  )}
                  <Link
                    to={`/learn/${course.slug}`}
                    className="mt-4 inline-flex items-center gap-2 rounded-full bg-ink px-5 py-2.5 text-[13px] text-cream transition hover:bg-[#2b241f]"
                  >
                    Открыть курс <ArrowRight size={14} />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Section>
  );
}

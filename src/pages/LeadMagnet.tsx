import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Send } from 'lucide-react';
import Seo from '../components/Seo';
import { getLeadMagnet } from '../data/leadMagnets';

export default function LeadMagnet() {
  const { slug } = useParams<{ slug: string }>();
  const magnet = getLeadMagnet(slug || '');

  if (!magnet) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-pink-50 to-white">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Материал не найден</h1>
          <Link to="/" className="text-pink-600 hover:text-pink-700">
            ← На главную
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-pink-50 to-white">
      <Seo
        title={`${magnet.title} — бесплатная шпаргалка | Alina Body`}
        description={magnet.description}
        path={`/lead/${magnet.slug}`}
        type="website"
      />
      <div className="container mx-auto px-4 py-12 max-w-3xl">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-gray-600 hover:text-pink-600 mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          На главную
        </Link>

        <h1 className="text-3xl md:text-5xl font-bold text-gray-900 mb-4">{magnet.title}</h1>
        <p className="text-lg text-gray-700 mb-2">{magnet.tagline}</p>
        <p className="text-gray-500 mb-10">{magnet.description}</p>

        <div className="space-y-6">
          {magnet.cards.map((card, i) => (
            <figure key={i} className="bg-white rounded-2xl shadow-md overflow-hidden">
              <img
                src={card.image}
                alt={card.title}
                loading="lazy"
                className="w-full h-auto"
              />
            </figure>
          ))}
        </div>

        <div className="mt-12 p-8 bg-gradient-to-r from-pink-100 to-pink-50 rounded-2xl border-2 border-pink-200 text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-3">Получи все материалы бесплатно</h2>
          <p className="text-gray-700 mb-6">
            Полный набор карточек и подробный разбор — в Telegram-канале Алины. Бесплатно и без давления.
          </p>
          <a
            href={magnet.tg}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 px-8 py-4 bg-pink-600 hover:bg-pink-700 text-white font-bold rounded-xl transition-colors"
          >
            <Send className="w-5 h-5" />
            Забрать в Telegram →
          </a>
        </div>
      </div>
    </div>
  );
}

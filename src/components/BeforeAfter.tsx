import { useState } from 'react';

type Props = {
  before: string;
  after: string;
  beforeLabel?: string;
  afterLabel?: string;
};

export default function BeforeAfter({ before, after, beforeLabel = 'До', afterLabel = 'После' }: Props) {
  const [pos, setPos] = useState(50);

  return (
    <div className="relative aspect-[4/5] w-full select-none overflow-hidden rounded-[28px] bg-cream">
      {/* after — подложка */}
      <img src={after} alt={afterLabel} draggable={false} className="absolute inset-0 h-full w-full object-cover" />
      {/* before — обрезается слева */}
      <div className="absolute inset-0 overflow-hidden" style={{ width: `${pos}%` }}>
        <img src={before} alt={beforeLabel} draggable={false} className="h-full w-full object-cover" style={{ width: '100%', maxWidth: 'none' }} />
      </div>
      {/* разделитель */}
      <div className="pointer-events-none absolute inset-y-0" style={{ left: `${pos}%` }}>
        <div className="absolute inset-y-0 -ml-px w-0.5 bg-white/90" />
        <div className="absolute top-1/2 -ml-4 -mt-4 flex h-8 w-8 items-center justify-center rounded-full bg-white text-[14px] text-ink shadow">
          ⇆
        </div>
      </div>
      {/* ползунок */}
      <input
        type="range"
        min={0}
        max={100}
        value={pos}
        onChange={(e) => setPos(Number(e.target.value))}
        className="absolute inset-0 h-full w-full cursor-ew-resize opacity-0"
        aria-label="Сравнение до и после"
      />
      <span className="pointer-events-none absolute left-4 top-4 rounded-full bg-ink/70 px-3 py-1 text-[11px] text-cream">
        {beforeLabel}
      </span>
      <span className="pointer-events-none absolute right-4 top-4 rounded-full bg-white/80 px-3 py-1 text-[11px] text-ink">
        {afterLabel}
      </span>
    </div>
  );
}

'use client';

import dynamic from 'next/dynamic';

const ThreeScene = dynamic(
  () => import('./ThreeScene'),
  { ssr: false }
);

export function ThreeBackground() {
  return (
    <div className="fixed inset-0 z-0 pointer-events-none opacity-40">
      <ThreeScene />
    </div>
  );
}

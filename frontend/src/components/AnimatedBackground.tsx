'use client';

import { useEffect, useRef } from 'react';

export function AnimatedBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animFrame: number;
    let time = 0;
    let mouseX = 0.5;
    let mouseY = 0.5;
    let lastFrame = 0;
    const FPS_INTERVAL = 1000 / 60;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    const particles: {
      x: number; y: number; vx: number; vy: number;
      size: number; alpha: number; phase: number;
    }[] = [];

    for (let i = 0; i < 25; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.2,
        vy: (Math.random() - 0.5) * 0.2,
        size: Math.random() * 2.5 + 0.8,
        alpha: Math.random() * 0.35 + 0.08,
        phase: Math.random() * Math.PI * 2,
      });
    }

    const orbs = [
      { x: 0.2, y: 0.3, rx: 0.3, ry: 0.25, c: '74,127,167', speed: 0.3 },
      { x: 0.7, y: 0.2, rx: 0.2, ry: 0.3, c: '179,207,229', speed: 0.2 },
      { x: 0.5, y: 0.7, rx: 0.35, ry: 0.2, c: '26,61,99', speed: 0.25 },
    ];

    const draw = (timestamp: number) => {
      if (document.hidden) {
        animFrame = requestAnimationFrame(draw);
        return;
      }

      const elapsed = timestamp - lastFrame;
      if (elapsed < FPS_INTERVAL) {
        animFrame = requestAnimationFrame(draw);
        return;
      }
      lastFrame = timestamp;

      time += 0.004;
      const w = canvas.width;
      const h = canvas.height;

      ctx.clearRect(0, 0, w, h);

      const mx = mouseX;
      const my = mouseY;

      // Orbs — blur kept moderate for performance
      ctx.filter = 'blur(60px)';
      for (const orb of orbs) {
        const cx = w * orb.x + Math.sin(time * orb.speed + orb.rx) * w * 0.08 + (mx - 0.5) * w * 0.02;
        const cy = h * orb.y + Math.cos(time * orb.speed * 0.7 + orb.ry) * h * 0.06 + (my - 0.5) * h * 0.02;
        const r = Math.min(w, h) * orb.rx;
        const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, r);
        const alpha = 0.12 + Math.sin(time * orb.speed + orb.rx) * 0.04;
        grad.addColorStop(0, `rgba(${orb.c},${alpha})`);
        grad.addColorStop(0.5, `rgba(${orb.c},${alpha * 0.4})`);
        grad.addColorStop(1, 'rgba(10,25,49,0)');
        ctx.beginPath();
        ctx.fillStyle = grad;
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.filter = 'none';

      // Bottom vignette
      const vig = ctx.createLinearGradient(0, h * 0.6, 0, h);
      vig.addColorStop(0, 'rgba(10,25,49,0)');
      vig.addColorStop(1, 'rgba(10,25,49,0.7)');
      ctx.fillStyle = vig;
      ctx.fillRect(0, h * 0.6, w, h * 0.4);

      // Particles — no blur, fewer, simpler
      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = w;
        if (p.x > w) p.x = 0;
        if (p.y < 0) p.y = h;
        if (p.y > h) p.y = 0;

        const a = p.alpha * (0.6 + 0.4 * Math.sin(time * 2 + p.phase));
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(179, 207, 229, ${a})`;
        ctx.fill();
      }

      animFrame = requestAnimationFrame(draw);
    };
    animFrame = requestAnimationFrame(draw);

    const onMouse = (e: MouseEvent) => {
      mouseX = e.clientX / window.innerWidth;
      mouseY = e.clientY / window.innerHeight;
    };
    window.addEventListener('mousemove', onMouse, { passive: true });

    return () => {
      cancelAnimationFrame(animFrame);
      window.removeEventListener('resize', resize);
      window.removeEventListener('mousemove', onMouse);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 -z-10 pointer-events-none"
      style={{ background: '#0A1931' }}
    />
  );
}

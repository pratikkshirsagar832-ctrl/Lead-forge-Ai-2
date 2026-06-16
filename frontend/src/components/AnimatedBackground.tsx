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

    /* ── ANIMATED GRID ── */
    const gridSize = 50;
    const gridPoints: { ox: number; oy: number; phase: number; speed: number }[] = [];
    for (let x = 0; x < canvas.width + gridSize; x += gridSize) {
      for (let y = 0; y < canvas.height + gridSize; y += gridSize) {
        gridPoints.push({
          ox: x, oy: y,
          phase: Math.random() * Math.PI * 2,
          speed: 0.3 + Math.random() * 0.4,
        });
      }
    }

    /* ── PREMIUM PARTICLES (80) ── */
    const particles: {
      x: number; y: number; vx: number; vy: number;
      size: number; alpha: number; phase: number; speed: number;
      orbit: number; orbitSpeed: number; orbitRadius: number;
    }[] = [];

    for (let i = 0; i < 80; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.12,
        vy: (Math.random() - 0.5) * 0.12,
        size: Math.random() * 2.5 + 0.4,
        alpha: Math.random() * 0.35 + 0.04,
        phase: Math.random() * Math.PI * 2,
        speed: 0.3 + Math.random() * 0.7,
        orbit: Math.random() * Math.PI * 2,
        orbitSpeed: 0.005 + Math.random() * 0.015,
        orbitRadius: 2 + Math.random() * 8,
      });
    }

    /* ── SHOOTING STARS ── */
    const shootingStars: {
      x: number; y: number; vx: number; vy: number;
      life: number; maxLife: number; tail: number; active: boolean;
    }[] = [];
    for (let i = 0; i < 3; i++) {
      shootingStars.push({
        x: 0, y: 0, vx: 0, vy: 0,
        life: 0, maxLife: 60 + Math.random() * 80,
        tail: 60 + Math.random() * 40, active: false,
      });
    }

    /* ── FLOATING GRADIENT ORBS (7) ── */
    const orbs = [
      { x: 0.15, y: 0.25, rx: 0.25, ry: 0.2, r: 0.32, c: '59,130,196', alpha: 0.14, speed: 0.25 },     // Steel
      { x: 0.78, y: 0.18, rx: 0.2, ry: 0.25, r: 0.28, c: '124,92,252', alpha: 0.12, speed: 0.2 },      // Violet
      { x: 0.5, y: 0.78, rx: 0.3, ry: 0.18, r: 0.35, c: '20,184,166', alpha: 0.1, speed: 0.22 },       // Teal
      { x: 0.88, y: 0.7, rx: 0.2, ry: 0.22, r: 0.22, c: '249,115,22', alpha: 0.07, speed: 0.18 },      // CTA Orange
      { x: 0.25, y: 0.82, rx: 0.22, ry: 0.28, r: 0.24, c: '244,63,94', alpha: 0.08, speed: 0.2 },      // Rose
      { x: 0.6, y: 0.3, rx: 0.18, ry: 0.2, r: 0.2, c: '168,85,247', alpha: 0.07, speed: 0.23 },        // Purple
      { x: 0.9, y: 0.4, rx: 0.2, ry: 0.18, r: 0.18, c: '250,204,21', alpha: 0.05, speed: 0.19 },       // Gold
    ];

    /* ── FLOATING SHAPES ── */
    const shapes: {
      x: number; y: number; size: number; type: 'circle' | 'diamond' | 'hexagon';
      alpha: number; phase: number; speed: number; rotation: number; rotSpeed: number;
    }[] = [];
    for (let i = 0; i < 12; i++) {
      const types = ['circle', 'diamond', 'hexagon'] as const;
      shapes.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: 6 + Math.random() * 14,
        type: types[Math.floor(Math.random() * 3)],
        alpha: 0.02 + Math.random() * 0.04,
        phase: Math.random() * Math.PI * 2,
        speed: 0.1 + Math.random() * 0.2,
        rotation: Math.random() * Math.PI * 2,
        rotSpeed: (Math.random() - 0.5) * 0.005,
      });
    }

    let shootTimer = 0;

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

      time += 0.003;
      const w = canvas.width;
      const h = canvas.height;
      const mx = mouseX;
      const my = mouseY;

      ctx.clearRect(0, 0, w, h);

      /* ── LAYER 1: Animated Grid ── */
      ctx.strokeStyle = 'rgba(59, 130, 196, 0.025)';
      ctx.lineWidth = 0.5;
      const gridOffset = Math.sin(time * 0.1) * 2;
      for (const gp of gridPoints) {
        const dx = gp.ox - w * mx * 0.02;
        const dy = gp.oy - h * my * 0.02;
        const sway = Math.sin(time * gp.speed + gp.phase) * gridOffset;
        ctx.beginPath();
        ctx.arc(dx, dy + sway, 0.5, 0, Math.PI * 2);
        ctx.stroke();
      }

      /* ── LAYER 2: Floating Geometric Shapes ── */
      for (const s of shapes) {
        s.rotation += s.rotSpeed;
        const swayX = Math.sin(time * s.speed + s.phase) * 8;
        const swayY = Math.cos(time * s.speed * 0.7 + s.phase * 1.3) * 6;
        const cx = s.x + swayX + (mx - 0.5) * w * 0.005;
        const cy = s.y + swayY + (my - 0.5) * h * 0.005;
        const a = s.alpha * (0.7 + 0.3 * Math.sin(time * s.speed + s.phase));

        ctx.save();
        ctx.translate(cx, cy);
        ctx.rotate(s.rotation);
        ctx.strokeStyle = `rgba(200, 220, 239, ${a})`;
        ctx.lineWidth = 0.8;

        if (s.type === 'circle') {
          ctx.beginPath();
          ctx.arc(0, 0, s.size, 0, Math.PI * 2);
          ctx.stroke();
        } else if (s.type === 'diamond') {
          ctx.beginPath();
          ctx.moveTo(0, -s.size);
          ctx.lineTo(s.size, 0);
          ctx.lineTo(0, s.size);
          ctx.lineTo(-s.size, 0);
          ctx.closePath();
          ctx.stroke();
        } else if (s.type === 'hexagon') {
          ctx.beginPath();
          for (let i = 0; i < 6; i++) {
            const angle = (Math.PI / 3) * i - Math.PI / 6;
            const px = Math.cos(angle) * s.size;
            const py = Math.sin(angle) * s.size;
            i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
          }
          ctx.closePath();
          ctx.stroke();
        }

        ctx.restore();

        // Wrap around
        s.x += (Math.random() - 0.5) * 0.1;
        s.y += (Math.random() - 0.5) * 0.1;
        if (s.x < -50) s.x = w + 50;
        if (s.x > w + 50) s.x = -50;
        if (s.y < -50) s.y = h + 50;
        if (s.y > h + 50) s.y = -50;
      }

      /* ── LAYER 3: Gradient Orbs ── */
      ctx.filter = 'blur(70px)';

      // Draw large ambient background orbs first (lower alpha)
      const ambientOrbs = [orbs[2], orbs[3], orbs[5]];
      for (const orb of ambientOrbs) {
        const cx = w * orb.x + Math.sin(time * orb.speed + orb.rx) * w * 0.07 + (mx - 0.5) * w * 0.012;
        const cy = h * orb.y + Math.cos(time * orb.speed * 0.7 + orb.ry) * h * 0.05 + (my - 0.5) * h * 0.012;
        const radius = Math.min(w, h) * orb.r;
        const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius);
        const alpha = orb.alpha * 0.6 + Math.sin(time * orb.speed + orb.rx) * 0.02;
        grad.addColorStop(0, `rgba(${orb.c},${alpha})`);
        grad.addColorStop(0.5, `rgba(${orb.c},${alpha * 0.4})`);
        grad.addColorStop(1, 'rgba(11,17,33,0)');
        ctx.beginPath();
        ctx.fillStyle = grad;
        ctx.arc(cx, cy, radius, 0, Math.PI * 2);
        ctx.fill();
      }

      // Draw primary orbs on top (higher alpha)
      for (let i = 0; i < orbs.length; i++) {
        const orb = orbs[i];
        const cx = w * orb.x + Math.sin(time * orb.speed + orb.rx + i) * w * 0.07 + (mx - 0.5) * w * 0.015;
        const cy = h * orb.y + Math.cos(time * orb.speed * 0.7 + orb.ry + i) * h * 0.05 + (my - 0.5) * h * 0.015;
        const radius = Math.min(w, h) * orb.r;
        const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius);
        const alpha = orb.alpha + Math.sin(time * orb.speed + orb.rx + i * 0.5) * 0.03;
        grad.addColorStop(0, `rgba(${orb.c},${alpha})`);
        grad.addColorStop(0.4, `rgba(${orb.c},${alpha * 0.5})`);
        grad.addColorStop(1, 'rgba(11,17,33,0)');
        ctx.beginPath();
        ctx.fillStyle = grad;
        ctx.arc(cx, cy, radius, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.filter = 'none';

      /* ── LAYER 4: Connection Lines ── */
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 120) {
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(124, 92, 252, ${0.03 * (1 - dist / 120)})`;
            ctx.lineWidth = 0.4;
            ctx.stroke();
          }
        }
      }

      /* ── LAYER 5: Particles ── */
      for (const p of particles) {
        p.orbit += p.orbitSpeed;
        const orbitalX = Math.cos(p.orbit) * p.orbitRadius;
        const orbitalY = Math.sin(p.orbit * 0.7) * p.orbitRadius * 0.5;

        p.x += p.vx + orbitalX * 0.01 + Math.sin(time * p.speed + p.phase) * 0.04;
        p.y += p.vy + orbitalY * 0.01 + Math.cos(time * p.speed * 0.8 + p.phase) * 0.04;

        // Wrap around with soft edge
        if (p.x < -10) p.x = w + 10;
        if (p.x > w + 10) p.x = -10;
        if (p.y < -10) p.y = h + 10;
        if (p.y > h + 10) p.y = -10;

        const a = p.alpha * (0.6 + 0.4 * Math.sin(time * 1.2 + p.phase));
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(200, 220, 239, ${a})`;
        ctx.fill();
      }

      /* ── LAYER 6: Shooting Stars ── */
      shootTimer += 0.003;
      if (shootTimer > 1) {
        shootTimer = 0;
        for (const ss of shootingStars) {
          if (!ss.active && Math.random() < 0.015) {
            ss.active = true;
            ss.life = 0;
            ss.maxLife = 60 + Math.random() * 80;
            const angle = -Math.PI / 4 + (Math.random() - 0.5) * 0.5;
            ss.x = Math.random() * w * 0.8 + w * 0.1;
            ss.y = Math.random() * h * 0.4;
            ss.vx = Math.cos(angle) * (3 + Math.random() * 2);
            ss.vy = Math.sin(angle) * (3 + Math.random() * 2);
            ss.tail = 40 + Math.random() * 40;
          }
        }
      }

      for (const ss of shootingStars) {
        if (!ss.active) continue;
        ss.life++;
        ss.x += ss.vx;
        ss.y += ss.vy;

        const progress = ss.life / ss.maxLife;
        const alpha = Math.sin(progress * Math.PI) * 0.6;

        // Tail
        ctx.beginPath();
        ctx.moveTo(ss.x, ss.y);
        ctx.lineTo(ss.x - ss.vx * ss.tail * 0.3, ss.y - ss.vy * ss.tail * 0.3);
        ctx.strokeStyle = `rgba(200, 220, 239, ${alpha})`;
        ctx.lineWidth = 1 + progress * 2;
        ctx.stroke();

        // Head glow
        ctx.beginPath();
        ctx.arc(ss.x, ss.y, 1.5, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(237, 242, 250, ${alpha * 0.8})`;
        ctx.fill();

        if (ss.life >= ss.maxLife) ss.active = false;
      }

      /* ── LAYER 7: Bottom Vignette ── */
      const vig = ctx.createLinearGradient(0, h * 0.4, 0, h);
      vig.addColorStop(0, 'rgba(11,17,33,0)');
      vig.addColorStop(0.4, 'rgba(11,17,33,0.2)');
      vig.addColorStop(1, 'rgba(11,17,33,0.85)');
      ctx.fillStyle = vig;
      ctx.fillRect(0, h * 0.4, w, h * 0.6);

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
      style={{ background: '#0B1121' }}
    />
  );
}

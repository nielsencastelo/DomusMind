"use client";

import { useEffect, useRef } from "react";

interface Particle {
  theta: number;
  phi: number;
}

export function MindSphere() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animFrame: number;
    let angleY = 0;
    let angleX = 0.15;

    function resize() {
      if (!canvas) return;
      canvas.width = canvas.offsetWidth * devicePixelRatio;
      canvas.height = canvas.offsetHeight * devicePixelRatio;
      ctx!.scale(devicePixelRatio, devicePixelRatio);
    }

    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    const NUM_POINTS = 90;
    const particles: Particle[] = Array.from({ length: NUM_POINTS }, (_, i) => ({
      theta: Math.acos(1 - (2 * (i + 0.5)) / NUM_POINTS),
      phi: Math.PI * (1 + Math.sqrt(5)) * i,
    }));

    function rotY(x: number, y: number, z: number, a: number) {
      return { x: x * Math.cos(a) + z * Math.sin(a), y, z: -x * Math.sin(a) + z * Math.cos(a) };
    }
    function rotX(x: number, y: number, z: number, a: number) {
      return { x, y: y * Math.cos(a) - z * Math.sin(a), z: y * Math.sin(a) + z * Math.cos(a) };
    }
    function project(x: number, y: number, z: number, R: number) {
      const fov = R * 3.5;
      const scale = fov / (fov + z);
      return { sx: x * scale, sy: y * scale, scale };
    }

    function draw() {
      const W = canvas!.offsetWidth;
      const H = canvas!.offsetHeight;
      ctx!.clearRect(0, 0, W, H);

      angleY += 0.0045;

      const R = Math.min(W, H) * 0.36;
      const cx = W / 2;
      const cy = H / 2;

      const pts = particles.map(({ theta, phi }) => {
        const x0 = R * Math.sin(theta) * Math.cos(phi);
        const y0 = R * Math.sin(theta) * Math.sin(phi);
        const z0 = R * Math.cos(theta);
        const ry = rotY(x0, y0, z0, angleY);
        const rx = rotX(ry.x, ry.y, ry.z, angleX);
        const p = project(rx.x, rx.y, rx.z, R);
        return { wx: rx.x, wy: rx.y, wz: rx.z, sx: cx + p.sx, sy: cy + p.sy, scale: p.scale };
      });

      // Draw connections
      const CONNECT_DIST = R * 0.55;
      for (let i = 0; i < pts.length; i++) {
        for (let j = i + 1; j < pts.length; j++) {
          const a = pts[i], b = pts[j];
          const d = Math.sqrt((a.wx - b.wx) ** 2 + (a.wy - b.wy) ** 2 + (a.wz - b.wz) ** 2);
          if (d > CONNECT_DIST) continue;
          const t = 1 - d / CONNECT_DIST;
          const avgScale = (a.scale + b.scale) / 2;
          const alpha = t * t * avgScale * 0.45;
          ctx!.beginPath();
          ctx!.strokeStyle = `rgba(0,212,255,${alpha.toFixed(3)})`;
          ctx!.lineWidth = t * 0.8;
          ctx!.moveTo(a.sx, a.sy);
          ctx!.lineTo(b.sx, b.sy);
          ctx!.stroke();
        }
      }

      // Draw core glow
      const coreGrad = ctx!.createRadialGradient(cx, cy, 0, cx, cy, R * 0.35);
      coreGrad.addColorStop(0, "rgba(0,212,255,0.07)");
      coreGrad.addColorStop(1, "transparent");
      ctx!.fillStyle = coreGrad;
      ctx!.beginPath();
      ctx!.arc(cx, cy, R * 0.35, 0, Math.PI * 2);
      ctx!.fill();

      // Draw particles (back to front)
      const sorted = [...pts].sort((a, b) => a.wz - b.wz);
      for (const p of sorted) {
        const brightness = (p.scale - 0.55) / 0.45;
        const alpha = Math.max(0, Math.min(1, brightness));
        const size = Math.max(0.8, p.scale * 2.2);

        // Halo
        const grad = ctx!.createRadialGradient(p.sx, p.sy, 0, p.sx, p.sy, size * 5);
        grad.addColorStop(0, `rgba(0,212,255,${(alpha * 0.35).toFixed(3)})`);
        grad.addColorStop(0.5, `rgba(139,92,246,${(alpha * 0.08).toFixed(3)})`);
        grad.addColorStop(1, "transparent");
        ctx!.fillStyle = grad;
        ctx!.beginPath();
        ctx!.arc(p.sx, p.sy, size * 5, 0, Math.PI * 2);
        ctx!.fill();

        // Core dot
        ctx!.fillStyle = `rgba(0,212,255,${alpha.toFixed(3)})`;
        ctx!.beginPath();
        ctx!.arc(p.sx, p.sy, size, 0, Math.PI * 2);
        ctx!.fill();
      }

      // Equator ring faint
      ctx!.save();
      ctx!.strokeStyle = "rgba(0,212,255,0.06)";
      ctx!.lineWidth = 1;
      ctx!.beginPath();
      ctx!.ellipse(cx, cy, R, R * Math.abs(Math.sin(angleX + Math.PI / 2)), 0, 0, Math.PI * 2);
      ctx!.stroke();
      ctx!.restore();

      animFrame = requestAnimationFrame(draw);
    }

    draw();

    return () => {
      cancelAnimationFrame(animFrame);
      ro.disconnect();
    };
  }, []);

  return <canvas ref={canvasRef} className="h-full w-full" />;
}

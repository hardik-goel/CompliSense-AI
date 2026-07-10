"use client";

import { Component, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Points, PointMaterial } from "@react-three/drei";
import type { Points as ThreePoints } from "three";

/** Distribute `count` points through a spherical shell of the given radius. */
function sphereShell(count: number, radius: number): Float32Array {
  const positions = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    const u = Math.random();
    const v = Math.random();
    const theta = 2 * Math.PI * u;
    const phi = Math.acos(2 * v - 1);
    // bias toward the surface so it reads as a sphere, not a filled ball
    const r = radius * Math.cbrt(0.72 + Math.random() * 0.28);
    positions[i * 3] = r * Math.sin(phi) * Math.cos(theta);
    positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
    positions[i * 3 + 2] = r * Math.cos(phi);
  }
  return positions;
}

function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mq.matches);
    const onChange = () => setReduced(mq.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);
  return reduced;
}

/**
 * three.js throws synchronously out of the WebGLRenderer constructor when a GL
 * context cannot be created, which happens in headless Chrome, on blocklisted
 * GPUs, and when a browser caps live contexts. Because that throw lands during
 * render, it escapes to the nearest error boundary — and with none present it
 * unmounted the whole page. Probe before mounting the Canvas.
 */
function useWebGLSupported(): boolean | null {
  const [supported, setSupported] = useState<boolean | null>(null);
  useEffect(() => {
    let ok = false;
    try {
      const probe = document.createElement("canvas");
      const gl = (probe.getContext("webgl2") ||
        probe.getContext("webgl")) as WebGLRenderingContext | null;
      ok = Boolean(gl);
      // Contexts are a scarce per-page resource; hand this one straight back.
      gl?.getExtension("WEBGL_lose_context")?.loseContext();
    } catch {
      ok = false;
    }
    setSupported(ok);
  }, []);
  return supported;
}

/** Last line of defence: a lost context mid-session must not take the page down. */
class CanvasErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    // The sphere is decorative (the host element is aria-hidden), so the
    // correct degraded state is simply nothing.
    return this.state.failed ? null : this.props.children;
  }
}

function Swarm({ reduced }: { reduced: boolean }) {
  const outer = useRef<ThreePoints>(null);
  const inner = useRef<ThreePoints>(null);
  const outerPts = useMemo(() => sphereShell(1600, 2.15), []);
  const innerPts = useMemo(() => sphereShell(900, 1.5), []);

  useFrame((state, delta) => {
    if (reduced) return;
    const d = Math.min(delta, 0.05); // clamp on tab refocus
    if (outer.current) {
      outer.current.rotation.y += d * 0.06;
      outer.current.rotation.x += d * 0.018;
    }
    if (inner.current) {
      inner.current.rotation.y -= d * 0.045;
    }
    // gentle parallax toward the pointer
    const px = state.pointer.x * 0.15;
    const py = state.pointer.y * 0.15;
    state.camera.position.x += (px - state.camera.position.x) * 0.04;
    state.camera.position.y += (py - state.camera.position.y) * 0.04;
    state.camera.lookAt(0, 0, 0);
  });

  return (
    <group>
      <Points ref={outer} positions={outerPts} stride={3} frustumCulled={false}>
        <PointMaterial
          transparent
          color="#3B82F6"
          size={0.02}
          sizeAttenuation
          depthWrite={false}
          opacity={0.9}
        />
      </Points>
      <Points ref={inner} positions={innerPts} stride={3} frustumCulled={false}>
        <PointMaterial
          transparent
          color="#22D3EE"
          size={0.016}
          sizeAttenuation
          depthWrite={false}
          opacity={0.8}
        />
      </Points>
    </group>
  );
}

export default function ParticleSphere() {
  const reduced = usePrefersReducedMotion();
  const webglSupported = useWebGLSupported();

  if (!webglSupported) return null;

  return (
    <CanvasErrorBoundary>
      <Canvas
        camera={{ position: [0, 0, 5], fov: 50 }}
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: true, powerPreference: "low-power" }}
        style={{ pointerEvents: "none" }}
        frameloop={reduced ? "demand" : "always"}
      >
        <Swarm reduced={reduced} />
      </Canvas>
    </CanvasErrorBoundary>
  );
}

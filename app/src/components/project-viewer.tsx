"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import * as THREE from "three";
import { Canvas, type ThreeEvent } from "@react-three/fiber";
import { Grid, OrbitControls, Text } from "@react-three/drei";
import { Bloom, EffectComposer, ToneMapping } from "@react-three/postprocessing";
import { ToneMappingMode } from "postprocessing";
import { X } from "lucide-react";

export type CandidatePart = {
  function?: string;
  mpn?: string;
  rationale?: string;
};

type ProjectViewerProps = {
  candidateParts: CandidatePart[];
};

const COLOR_BY_TYPE: Record<string, string> = {
  mcu: "#34d399",
  microcontroller: "#34d399",
  controller: "#34d399",
  sensor: "#60a5fa",
  power: "#fb923c",
  battery: "#fb923c",
  charger: "#fb923c",
  regulator: "#fb923c",
  comm: "#a78bfa",
  communication: "#a78bfa",
  wifi: "#a78bfa",
  bluetooth: "#a78bfa",
  radio: "#a78bfa",
  driver: "#f472b6",
  motor: "#f472b6",
  pump: "#f472b6",
  actuator: "#f472b6",
  default: "#94a3b8",
};

function colorFor(part: CandidatePart): string {
  const fn = (part.function ?? "").toLowerCase();
  for (const [key, color] of Object.entries(COLOR_BY_TYPE)) {
    if (fn.includes(key)) return color;
  }
  return COLOR_BY_TYPE.default;
}

const COLS = 4;
const SPACING_X = 1.8;
const SPACING_Z = 1.8;

type RendererMode = "webgl" | "webgpu" | "detecting";

async function buildWebGPURenderer(props: unknown): Promise<unknown> {
  const mod = (await import("three/webgpu")) as typeof import("three/webgpu");
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const renderer = new mod.WebGPURenderer(props as any);
  await renderer.init();
  return renderer;
}

function PartBox({
  part,
  position,
  selected,
  onPick,
}: {
  part: CandidatePart;
  position: [number, number, number];
  selected: boolean;
  onPick: (p: CandidatePart) => void;
}) {
  const [hover, setHover] = useState(false);
  const color = colorFor(part);
  const handleClick = (e: ThreeEvent<MouseEvent>) => {
    e.stopPropagation();
    onPick(part);
  };
  return (
    <group position={position}>
      <mesh
        onClick={handleClick}
        onPointerOver={(e) => {
          e.stopPropagation();
          setHover(true);
          document.body.style.cursor = "pointer";
        }}
        onPointerOut={() => {
          setHover(false);
          document.body.style.cursor = "";
        }}
        castShadow
      >
        <boxGeometry args={[1.1, 0.5, 1.1]} />
        <meshStandardMaterial
          color={color}
          emissive={selected ? color : "#000000"}
          emissiveIntensity={selected ? 1.2 : 0}
          metalness={0.25}
          roughness={0.4}
          opacity={hover || selected ? 1 : 0.92}
          transparent
        />
      </mesh>
      <Text
        position={[0, 0.55, 0]}
        fontSize={0.16}
        color="#fafafa"
        anchorX="center"
        anchorY="bottom"
        maxWidth={1.6}
      >
        {part.mpn ?? "—"}
      </Text>
      {part.function ? (
        <Text
          position={[0, -0.32, 0]}
          fontSize={0.1}
          color="#a3a3a3"
          anchorX="center"
          anchorY="top"
          maxWidth={1.6}
        >
          {part.function}
        </Text>
      ) : null}
    </group>
  );
}

function useIsMobile(): boolean {
  const [mobile, setMobile] = useState(false);
  useEffect(() => {
    if (typeof window === "undefined") return;
    const mq = window.matchMedia("(max-width: 768px)");
    setMobile(mq.matches);
    const handle = (e: MediaQueryListEvent) => setMobile(e.matches);
    mq.addEventListener("change", handle);
    return () => mq.removeEventListener("change", handle);
  }, []);
  return mobile;
}

export function ProjectViewer({ candidateParts }: ProjectViewerProps) {
  const [selected, setSelected] = useState<CandidatePart | null>(null);
  const [mode, setMode] = useState<RendererMode>("detecting");
  const isMobile = useIsMobile();

  // Detect WebGPU once on mount. Falls back to WebGL2 if the navigator
  // API is missing, requestAdapter returns null, or feature-detect throws.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const gpu: any = (navigator as any).gpu;
        if (!gpu || typeof gpu.requestAdapter !== "function") {
          if (!cancelled) setMode("webgl");
          return;
        }
        const adapter = await gpu.requestAdapter();
        if (!cancelled) setMode(adapter ? "webgpu" : "webgl");
      } catch {
        if (!cancelled) setMode("webgl");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const positions = useMemo<[number, number, number][]>(() => {
    return candidateParts.map((_, i) => {
      const col = i % COLS;
      const row = Math.floor(i / COLS);
      return [
        (col - (COLS - 1) / 2) * SPACING_X,
        0,
        (row - 0.5) * SPACING_Z,
      ];
    });
  }, [candidateParts]);

  if (candidateParts.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-neutral-800 bg-neutral-900/30 p-10 text-center text-sm text-neutral-400">
        No design to render yet. Run the agent to generate a candidate parts
        list.
      </div>
    );
  }

  if (mode === "detecting") {
    return (
      <div className="flex h-[440px] w-full items-center justify-center rounded-2xl border border-neutral-800 bg-neutral-950 text-sm text-neutral-500">
        Initializing renderer…
      </div>
    );
  }

  return (
    <div className="relative h-[440px] w-full overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-950">
      <Canvas
        key={mode}
        shadows={!isMobile}
        dpr={isMobile ? [1, 1.5] : [1, 2]}
        camera={{ position: [4, 4, 6], fov: 45 }}
        gl={
          mode === "webgpu"
            ? // eslint-disable-next-line @typescript-eslint/no-explicit-any
              (buildWebGPURenderer as any)
            : { antialias: true, powerPreference: "high-performance" }
        }
        onCreated={({ gl }) => {
          gl.toneMapping = THREE.ACESFilmicToneMapping;
          gl.toneMappingExposure = 1.05;
        }}
      >
        <color attach="background" args={["#0a0a0a"]} />
        <ambientLight intensity={0.45} />
        <directionalLight
          position={[6, 8, 4]}
          intensity={1.1}
          castShadow={!isMobile}
          shadow-mapSize-width={isMobile ? 512 : 1024}
          shadow-mapSize-height={isMobile ? 512 : 1024}
        />
        <Suspense fallback={null}>
          {candidateParts.map((part, i) => (
            <PartBox
              key={`${part.mpn ?? "_"}-${i}`}
              part={part}
              position={positions[i]}
              selected={
                selected?.mpn === part.mpn && selected?.function === part.function
              }
              onPick={(p) => setSelected(p)}
            />
          ))}
        </Suspense>
        <Grid
          args={[20, 20]}
          cellSize={0.5}
          cellColor="#262626"
          sectionSize={2}
          sectionColor="#404040"
          fadeDistance={18}
          infiniteGrid
          position={[0, -0.26, 0]}
        />
        <OrbitControls
          makeDefault
          enableDamping
          dampingFactor={0.08}
          minDistance={3}
          maxDistance={20}
          target={[0, 0, 0]}
        />
        {mode === "webgl" ? (
          <EffectComposer multisampling={isMobile ? 0 : 4}>
            <Bloom
              intensity={0.7}
              luminanceThreshold={0.3}
              luminanceSmoothing={0.6}
              mipmapBlur
            />
            <ToneMapping mode={ToneMappingMode.ACES_FILMIC} />
          </EffectComposer>
        ) : null}
      </Canvas>

      <div className="pointer-events-none absolute left-4 top-4 flex items-center gap-2">
        <span className="rounded-full border border-white/10 bg-black/40 px-3 py-1 text-xs text-neutral-300 backdrop-blur">
          Placeholder geometry · {candidateParts.length} part
          {candidateParts.length === 1 ? "" : "s"}
        </span>
        <span
          className={
            mode === "webgpu"
              ? "rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-[10px] uppercase tracking-wider text-emerald-300 backdrop-blur"
              : "rounded-full border border-white/10 bg-black/40 px-2.5 py-1 text-[10px] uppercase tracking-wider text-neutral-400 backdrop-blur"
          }
        >
          {mode === "webgpu" ? "WebGPU" : "WebGL2"}
        </span>
      </div>

      {selected ? (
        <aside className="absolute right-4 top-4 max-w-xs rounded-xl border border-neutral-800 bg-neutral-900/90 p-4 text-sm text-neutral-200 shadow-xl backdrop-blur">
          <div className="flex items-start justify-between gap-3">
            <div className="flex flex-col">
              {selected.function ? (
                <span className="text-xs uppercase tracking-wider text-neutral-500">
                  {selected.function}
                </span>
              ) : null}
              <span className="font-mono text-base text-white">
                {selected.mpn ?? "—"}
              </span>
            </div>
            <button
              type="button"
              onClick={() => setSelected(null)}
              className="rounded-md p-1 text-neutral-500 hover:bg-neutral-800 hover:text-white"
              aria-label="Close"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
          {selected.rationale ? (
            <p className="mt-3 text-xs leading-relaxed text-neutral-300">
              {selected.rationale}
            </p>
          ) : null}
        </aside>
      ) : null}
    </div>
  );
}

export default ProjectViewer;

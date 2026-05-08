"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import * as THREE from "three";
import { Canvas, type ThreeEvent } from "@react-three/fiber";
import { Bounds, Grid, OrbitControls, Text, useGLTF } from "@react-three/drei";
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
  glbBase64?: string;
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

// WebGPU detection removed: drei's <Text> uses ShaderMaterial which is
// incompatible with three's WebGPU/TSL backend (browser console threw
// "Material 'ShaderMaterial' is not compatible" + drawIndexed errors on
// the user's tier-1 test). WebGL2 with EffectComposer postprocessing is
// strictly the better path for this viewer; revisit when drei has
// first-class WebGPU support.

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

function GLBModel({ url }: { url: string }) {
  const { scene } = useGLTF(url);
  // Clone so multiple mounts don't share mutable transforms; lazy-clone
  // on first render keeps drei's cache happy.
  const cloned = useMemo(() => scene.clone(true), [scene]);
  return <primitive object={cloned} />;
}

function useGlbObjectUrl(glbBase64: string | undefined): string | undefined {
  const [url, setUrl] = useState<string | undefined>(undefined);
  useEffect(() => {
    if (!glbBase64) {
      setUrl(undefined);
      return;
    }
    const binary = atob(glbBase64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    const blob = new Blob([bytes], { type: "model/gltf-binary" });
    const objectUrl = URL.createObjectURL(blob);
    setUrl(objectUrl);
    return () => {
      URL.revokeObjectURL(objectUrl);
    };
  }, [glbBase64]);
  return url;
}

export function ProjectViewer({
  candidateParts,
  glbBase64,
}: ProjectViewerProps) {
  const [selected, setSelected] = useState<CandidatePart | null>(null);
  const isMobile = useIsMobile();
  const glbUrl = useGlbObjectUrl(glbBase64);
  const showGlb = Boolean(glbUrl);

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

  const hasContent = showGlb || candidateParts.length > 0;

  if (!hasContent) {
    return (
      <div className="rounded-2xl border border-dashed border-neutral-800 bg-neutral-900/30 p-10 text-center text-sm text-neutral-400">
        No design to render yet. Run the agent to generate a candidate parts
        list.
      </div>
    );
  }

  return (
    <div className="relative h-[440px] w-full overflow-hidden rounded-2xl border border-neutral-800 bg-neutral-950">
      <Canvas
        shadows={!isMobile}
        dpr={isMobile ? [1, 1.5] : [1, 2]}
        camera={{ position: [4, 4, 6], fov: 45 }}
        gl={{ antialias: true, powerPreference: "high-performance" }}
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
        {showGlb && glbUrl ? (
          <Suspense fallback={null}>
            <Bounds fit clip observe margin={1.2}>
              <GLBModel url={glbUrl} />
            </Bounds>
          </Suspense>
        ) : (
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
        )}
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
          minDistance={1}
          maxDistance={50}
          target={[0, 0, 0]}
        />
        <EffectComposer multisampling={isMobile ? 0 : 4}>
          <Bloom
            intensity={0.7}
            luminanceThreshold={0.3}
            luminanceSmoothing={0.6}
            mipmapBlur
          />
          <ToneMapping mode={ToneMappingMode.ACES_FILMIC} />
        </EffectComposer>
      </Canvas>

      <div className="pointer-events-none absolute left-4 top-4 flex items-center gap-2">
        <span className="rounded-full border border-white/10 bg-black/40 px-3 py-1 text-xs text-neutral-300 backdrop-blur">
          {showGlb
            ? "Mechanical CAD geometry (build123d STEP -> GLB)"
            : `Placeholder geometry · ${candidateParts.length} part${candidateParts.length === 1 ? "" : "s"}`}
        </span>
        <span className="rounded-full border border-white/10 bg-black/40 px-2.5 py-1 text-[10px] uppercase tracking-wider text-neutral-400 backdrop-blur">
          WebGL2
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

import { useEffect, useMemo, useRef, useState } from 'react';
import { ErrorMessage, Spinner } from '../common/Feedback.jsx';
import { api } from '../../services/api.js';

const SIZE = 320;
const ATOM_RADIUS = 9;

// Colour per element from its symbol, so each element keeps the same colour everywhere.
const colourOf = (symbol) => {
  let hash = 0;
  for (const ch of symbol) hash = (hash * 31 + ch.charCodeAt(0)) % 360;
  return `hsl(${hash}, 60%, 55%)`;
};

const rotate = ([x, y, z], yaw, pitch) => {
  const x1 = x * Math.cos(yaw) + z * Math.sin(yaw);
  const z1 = -x * Math.sin(yaw) + z * Math.cos(yaw);
  const y2 = y * Math.cos(pitch) - z1 * Math.sin(pitch);
  const z2 = y * Math.sin(pitch) + z1 * Math.cos(pitch);
  return [x1, y2, z2];
};

/** Cartesian atom positions and unit-cell corners, centred on the cell centre. */
function geometry(structure) {
  const { lattice_mat: lat, coords, elements, cartesian } = structure;
  const toCart = (frac) => [0, 1, 2].map((k) => frac[0] * lat[0][k] + frac[1] * lat[1][k] + frac[2] * lat[2][k]);
  const atoms = coords.map((c, i) => ({ pos: cartesian ? c : toCart(c), symbol: elements[i] }));
  // Corners keep their integer (i, j, k) so edges join corners that differ in exactly one index.
  const corners = [];
  for (const i of [0, 1]) for (const j of [0, 1]) for (const k of [0, 1]) corners.push({ idx: [i, j, k], pos: toCart([i, j, k]) });
  const centre = [0, 1, 2].map((d) => corners.reduce((s, c) => s + c.pos[d], 0) / corners.length);
  const shift = (p) => p.map((v, d) => v - centre[d]);
  const edges = [];
  corners.forEach((a, ia) => corners.forEach((b, ib) => {
    const differing = a.idx.filter((v, d) => v !== b.idx[d]).length;
    if (ib > ia && differing === 1) edges.push([shift(a.pos), shift(b.pos)]);
  }));
  const scale = Math.max(...corners.map((c) => Math.hypot(...shift(c.pos))), 1e-9);
  return {
    atoms: atoms.map((a) => ({ ...a, pos: shift(a.pos) })),
    edges,
    scale,
  };
}

export default function StructureViewer({ materialId }) {
  const [state, setState] = useState({ loading: true, data: null, error: null });
  const [angles, setAngles] = useState({ yaw: 0.6, pitch: -0.4 });
  const drag = useRef(null);

  useEffect(() => {
    const controller = new AbortController();
    setState({ loading: true, data: null, error: null });
    api(`/materials/${materialId}/structure`, { signal: controller.signal })
      .then((data) => setState({ loading: false, data, error: null }))
      .catch((error) => { if (error.name !== 'AbortError') setState({ loading: false, data: null, error }); });
    return () => controller.abort();
  }, [materialId]);

  const geo = useMemo(() => (state.data ? geometry(state.data) : null), [state.data]);
  if (state.loading) return <Spinner label="Loading structure…" />;
  if (state.error) return <p className="muted">{state.error.message}</p>;
  if (!geo) return null;

  const px = (p) => (SIZE / 2) + (p[0] / geo.scale) * (SIZE * 0.4);
  const py = (p) => (SIZE / 2) - (p[1] / geo.scale) * (SIZE * 0.4);
  const projected = geo.atoms
    .map((a) => ({ ...a, r: rotate(a.pos, angles.yaw, angles.pitch) }))
    .sort((a, b) => a.r[2] - b.r[2]);
  const edgesProjected = geo.edges.map(([a, b]) => [rotate(a, angles.yaw, angles.pitch), rotate(b, angles.yaw, angles.pitch)]);

  const onPointerDown = (e) => { drag.current = { x: e.clientX, y: e.clientY, ...angles }; e.currentTarget.setPointerCapture(e.pointerId); };
  const onPointerMove = (e) => {
    if (!drag.current) return;
    const dx = e.clientX - drag.current.x;
    const dy = e.clientY - drag.current.y;
    setAngles({ yaw: drag.current.yaw + dx * 0.01, pitch: drag.current.pitch + dy * 0.01 });
  };
  const onPointerUp = () => { drag.current = null; };

  return (
    <figure className="structure">
      <svg
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        width="100%"
        role="img"
        aria-label={`Crystal structure of ${state.data.formula}, drag to rotate`}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerLeave={onPointerUp}
        style={{ touchAction: 'none', cursor: 'grab', maxWidth: SIZE }}
      >
        {edgesProjected.map(([a, b], i) => (
          <line key={i} x1={px(a)} y1={py(a)} x2={px(b)} y2={py(b)} stroke="currentColor" strokeOpacity="0.35" />
        ))}
        {projected.map((a, i) => (
          <g key={i}>
            <circle cx={px(a.r)} cy={py(a.r)} r={ATOM_RADIUS} fill={colourOf(a.symbol)} stroke="#0003" />
            <text x={px(a.r)} y={py(a.r) + 3} fontSize="8" textAnchor="middle" fill="#000a">{a.symbol}</text>
          </g>
        ))}
      </svg>
      <figcaption className="muted small">
        {state.data.elements.length} atoms in the unit cell (JARVIS {state.data.jid}). Drag to rotate; the cell
        is shown without periodic images.
      </figcaption>
    </figure>
  );
}

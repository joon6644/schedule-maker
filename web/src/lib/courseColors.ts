/** 강의명 → 시간표 팔레트 색 (tokens.css 의 --color-course-N-*) */
const PALETTE_SIZE = 8

export function colorIndex(name: string, assigned?: Map<string, number>): number {
  if (assigned?.has(name)) return assigned.get(name)!
  let hash = 0
  for (let i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) | 0
  return (Math.abs(hash) % PALETTE_SIZE) + 1
}

/** 한 시간표 안에서는 가능한 한 서로 다른 색이 되도록 배정 */
export function assignColors(names: string[]): Map<string, number> {
  const result = new Map<string, number>()
  const used = new Set<number>()
  for (const name of [...names].sort()) {
    let idx = colorIndex(name)
    for (let k = 0; k < PALETTE_SIZE && used.has(idx); k++) idx = (idx % PALETTE_SIZE) + 1
    used.add(idx)
    result.set(name, idx)
  }
  return result
}

export function courseColorVars(idx: number) {
  return {
    bg: `var(--color-course-${idx}-bg)`,
    fg: `var(--color-course-${idx}-fg)`,
    bar: `var(--color-course-${idx}-bar)`,
  }
}

import { Bookmark, Pencil } from 'lucide-react'
import { useMemo, useRef, useState } from 'react'
import { cx, EmptyState, IconButton, RemoveButton, Section, type ToastData } from '../components/ui'
import type { CourseData } from '../engine/types'
import { useSaved, useStore, type SavedSchedule } from '../lib/store'

/**
 * 저장한 시간표 관리 — 눌러서 열기(다시 누르면 닫기), 이름 바꾸기, 삭제(되돌리기 가능)
 */
export function SavedPanel({ courses, activeId, onOpen, notify }: {
  courses: CourseData[]
  activeId: string | null
  onOpen: (id: string | null) => void
  notify: (message: string, action?: ToastData['action']) => void
}) {
  const saved = useSaved()
  const { dispatch } = useStore()
  const byId = useMemo(() => new Map(courses.map((c) => [c.id, c])), [courses])
  const [editing, setEditing] = useState<string | null>(null)

  if (saved.length === 0) {
    return <EmptyState icon={<Bookmark size={36} strokeWidth={1.5} />} title="저장한 시간표가 없어요" />
  }

  const remove = (s: SavedSchedule) => {
    dispatch({ type: 'removeSaved', id: s.id })
    if (s.id === activeId) onOpen(null)
    notify(`'${s.name}' 삭제함`, { label: '되돌리기', onClick: () => dispatch({ type: 'saveSchedule', schedule: s }) })
  }

  return (
    <div className="px-4 pt-1 pb-6">
      <Section flush>
        {saved.map((s) => {
          const active = s.id === activeId
          const names = s.courseIds.map((id) => byId.get(id)?.name).filter(Boolean)
          return (
            <div key={s.id} className={cx('flex items-center gap-1 rounded-md pr-2 transition-colors', active ? 'bg-surface-sunken' : 'hover:bg-surface-hover')}>
              {editing === s.id ? (
                <RenameInput
                  initial={s.name}
                  onDone={(name) => {
                    if (name) dispatch({ type: 'renameSaved', id: s.id, name })
                    setEditing(null)
                  }}
                />
              ) : (
                <button type="button" onClick={() => onOpen(active ? null : s.id)} aria-pressed={active} className="min-w-0 flex-1 py-2.5 pl-4 text-left">
                  <span className={cx('block truncate text-[15px] font-semibold tracking-tight', active && 'text-accent-fg')}>{s.name}</span>
                  <span className="block truncate text-[13px] text-fg-muted">
                    {s.totalCredits}학점 · {names.join(', ')}
                  </span>
                </button>
              )}
              {editing !== s.id && (
                <IconButton label="이름 바꾸기" size="sm" onClick={() => setEditing(s.id)}>
                  <Pencil size={14} />
                </IconButton>
              )}
              <RemoveButton onClick={() => remove(s)} />
            </div>
          )
        })}
      </Section>
    </div>
  )
}

/** Enter·바깥 클릭 = 확정, Esc = 취소 */
function RenameInput({ initial, onDone }: { initial: string; onDone: (name: string | null) => void }) {
  const [value, setValue] = useState(initial)
  // Esc 로 닫힐 때 뒤따르는 blur 가 다시 저장하지 않도록
  const finished = useRef(false)
  const finish = (name: string | null) => {
    if (finished.current) return
    finished.current = true
    onDone(name)
  }
  return (
    <input
      autoFocus
      value={value}
      onChange={(e) => setValue(e.target.value)}
      onFocus={(e) => e.target.select()}
      onBlur={() => finish(value.trim() || null)}
      onKeyDown={(e) => {
        if (e.key === 'Enter') e.currentTarget.blur()
        if (e.key === 'Escape') finish(null)
      }}
      maxLength={30}
      aria-label="시간표 이름"
      className="my-1.5 ml-2 h-9 min-w-0 flex-1 rounded-md bg-surface-sunken px-2 text-[15px] font-semibold outline-none focus:ring-2 focus:ring-accent-soft"
    />
  )
}

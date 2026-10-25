import { Bookmark, Pencil } from 'lucide-react'
import { useMemo, useRef, useState, type ReactNode } from 'react'
import { cx, EmptyState, IconButton, RemoveButton, Section, type ToastData } from '../components/ui'
import type { CourseData } from '../engine/types'
import { useSaved, useStore, type SavedSchedule } from '../lib/store'

type Notify = (message: string, action?: ToastData['action']) => void

/** 저장한 시간표 관리 — 눌러서 열기(다시 누르면 닫기), 이름 바꾸기, 삭제(되돌리기 가능) */
export function SavedPanel({ courses, activeId, onOpen, notify }: {
  courses: CourseData[]
  /** 지금 열어 둔 저장한 시간표 */
  activeId: string | null
  onOpen: (id: string | null) => void
  notify: Notify
}) {
  const saved = useSaved()
  const { dispatch } = useStore()
  const byId = useMemo(() => new Map(courses.map((c) => [c.id, c])), [courses])

  const remove = (s: SavedSchedule) => {
    dispatch({ type: 'removeSaved', id: s.id })
    if (s.id === activeId) onOpen(null)
    notify(`'${s.name}' 삭제함`, { label: '되돌리기', onClick: () => dispatch({ type: 'saveSchedule', schedule: s }) })
  }

  if (saved.length === 0) {
    return <EmptyState icon={<Bookmark size={36} strokeWidth={1.5} />} title="저장한 시간표가 없어요" />
  }

  return (
    <div className="px-4 pt-1 pb-6">
      <Section flush>
        {saved.map((s) => {
          const active = s.id === activeId
          return (
            <SavedRow
              key={s.id}
              name={s.name}
              detail={`${s.totalCredits}학점 · ${s.courseIds.map((id) => byId.get(id)?.name).filter(Boolean).join(', ')}`}
              active={active}
              onClick={() => onOpen(active ? null : s.id)}
              onRename={(name) => dispatch({ type: 'renameSaved', id: s.id, name })}
              onRemove={() => remove(s)}
            />
          )
        })}
      </Section>
    </div>
  )
}

/** 저장한 항목 한 줄: 눌러서 열기/적용, 이름 바꾸기, 삭제 */
export function SavedRow({ name, detail, active, activeMark, onClick, onRename, onRemove }: {
  name: string
  detail: string
  active: boolean
  /** 활성 표시를 배경 대신 아이콘으로 (조건: 지금 적용된 것) */
  activeMark?: ReactNode
  onClick: () => void
  onRename: (name: string) => void
  onRemove: () => void
}) {
  const [editing, setEditing] = useState(false)
  const highlight = active && !activeMark
  return (
    <div className={cx('flex items-center gap-1 rounded-md pr-2 transition-colors', highlight ? 'bg-surface-sunken' : 'hover:bg-surface-hover')}>
      {editing ? (
        <RenameInput
          initial={name}
          onDone={(next) => {
            if (next) onRename(next)
            setEditing(false)
          }}
        />
      ) : (
        <button type="button" onClick={onClick} aria-pressed={active} className="min-w-0 flex-1 py-2.5 pl-4 text-left">
          <span className="flex items-center gap-1.5">
            <span className={cx('truncate text-[15px] font-semibold tracking-tight', highlight && 'text-accent-fg')}>{name}</span>
            {active && activeMark}
          </span>
          <span className="block truncate text-[13px] text-fg-muted">{detail}</span>
        </button>
      )}
      {!editing && (
        <IconButton label="이름 바꾸기" size="sm" onClick={() => setEditing(true)}>
          <Pencil size={14} />
        </IconButton>
      )}
      <RemoveButton onClick={onRemove} />
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
      aria-label="이름"
      className="my-1.5 ml-2 h-9 min-w-0 flex-1 rounded-md bg-surface-sunken px-2 text-[15px] font-semibold outline-none focus:ring-2 focus:ring-accent-soft"
    />
  )
}

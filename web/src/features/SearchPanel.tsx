import { Check, Search, X } from 'lucide-react'
import { useDeferredValue, useMemo, useState } from 'react'
import { Badge, Button, cx, EmptyState, IconButton, Segmented } from '../components/ui'
import { matchesFilter, timeSummary } from '../engine/course'
import type { CourseData, CourseFilter } from '../engine/types'
import { useConfig, useStore, type ListType } from '../lib/store'

const PAGE = 60

function normalize(text: string) {
  return text.toLowerCase().replace(/\s+/g, '')
}

export function SearchPanel({ courses }: { courses: CourseData[] }) {
  const { dispatch } = useStore()
  const config = useConfig()
  const [query, setQuery] = useState('')
  const [target, setTarget] = useState<ListType>('desired')
  const [expanded, setExpanded] = useState<string | null>(null)
  const [limit, setLimit] = useState(PAGE)
  const deferredQuery = useDeferredValue(query)

  const results = useMemo(() => {
    const keywords = deferredQuery.split(/\s+/).filter(Boolean).map(normalize)
    const matched = keywords.length
      ? courses.filter((c) => {
          const hay = normalize(`${c.name} ${c.professor} ${c.id}`)
          return keywords.every((k) => hay.includes(k))
        })
      : courses
    // 강의명이 검색어로 시작하는 강의 우선
    const first = keywords[0]
    return [...matched].sort((a, b) => {
      if (first) {
        const sa = normalize(a.name).startsWith(first) ? 0 : 1
        const sb = normalize(b.name).startsWith(first) ? 0 : 1
        if (sa !== sb) return sa - sb
      }
      return a.name.localeCompare(b.name, 'ko') || a.id.localeCompare(b.id)
    })
  }, [courses, deferredQuery])

  const membership = (course: CourseData): ListType | null => {
    if (config.required.some((f) => matchesFilter(f, course))) return 'required'
    if (config.desired.some((f) => matchesFilter(f, course))) return 'desired'
    return null
  }

  const add = (filter: CourseFilter) => {
    dispatch({ type: 'addFilter', list: target, filter })
    setExpanded(null)
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="space-y-3 px-4 pt-1 pb-3">
        {/* iOS 검색 필드: 채워진 배경, 테두리 없음 */}
        <div className="relative">
          <Search size={16} className="pointer-events-none absolute top-1/2 left-2.5 -translate-y-1/2 text-fg-subtle" />
          <input
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
              setLimit(PAGE)
            }}
            placeholder="강의명, 교수명, 강의번호"
            aria-label="강의 검색"
            className="h-9 w-full rounded-md bg-surface-sunken pr-9 pl-8 text-[15px] outline-none placeholder:text-fg-subtle focus:ring-2 focus:ring-accent-soft"
          />
          {query && (
            <IconButton label="검색어 지우기" size="sm" className="absolute top-1/2 right-1 -translate-y-1/2 size-6" onClick={() => setQuery('')}>
              <X size={13} />
            </IconButton>
          )}
        </div>
        <div className="flex items-center justify-between gap-3">
          <span className="text-[13px] text-fg-muted tabular-nums">{results.length.toLocaleString()}개 강의</span>
          <Segmented
            size="sm"
            value={target}
            onChange={setTarget}
            className="w-44"
            options={[
              { value: 'required', label: <><Dot tone="required" />필수로</> },
              { value: 'desired', label: <><Dot tone="desired" />희망으로</> },
            ]}
          />
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-2 pb-4">
        {results.length === 0 ? (
          <EmptyState icon={<Search size={36} strokeWidth={1.5} />} title="검색 결과 없음" description="띄어쓰기로 여러 단어를 함께 검색할 수 있어요." />
        ) : (
          <ul className="space-y-0.5">
            {results.slice(0, limit).map((course) => {
              const member = membership(course)
              const open = expanded === course.id
              return (
                <li key={course.id} className={cx('rounded-md transition-colors', open ? 'bg-surface-raised shadow-sm' : 'hover:bg-surface-hover')}>
                  <button
                    type="button"
                    onClick={() => setExpanded(open ? null : course.id)}
                    aria-expanded={open}
                    className="flex w-full items-start gap-3 px-3 py-2.5 text-left"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-x-1.5 gap-y-0.5">
                        <span className="min-w-0 text-[15px] leading-snug font-semibold tracking-tight break-keep [overflow-wrap:anywhere]">{course.name}</span>
                        {member && (
                          <Badge tone={member}>
                            <Check size={10} strokeWidth={3.5} />
                            {member === 'required' ? '필수' : '희망'}
                          </Badge>
                        )}
                      </div>
                      <div className="mt-0.5 truncate text-[13px] text-fg-muted">
                        {course.professor || '교수 미정'} · {course.credits}학점 · {timeSummary(course)}
                      </div>
                    </div>
                    <span className="mt-0.5 shrink-0 text-[12px] text-fg-subtle tabular-nums">#{course.id}</span>
                  </button>
                  {open && <AddOptions course={course} courses={courses} target={target} onAdd={add} />}
                </li>
              )
            })}
          </ul>
        )}
        {results.length > limit && (
          <div className="flex justify-center pt-3">
            <Button variant="ghost" onClick={() => setLimit((l) => l + PAGE)}>
              {(results.length - limit).toLocaleString()}개 더 보기
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * 담을 때 분반을 얼마나 정할지 고르기
 * - 분반 상관없이: 같은 과목의 어느 분반이든 (시간표에 맞는 걸로 자동)
 * - ○○ 교수님 분반만: 그 교수님 분반 중에서
 * - 이 분반만: 지금 보고 있는 분반 하나
 * 분반이 하나뿐이면 고를 필요 없이 바로 담기
 */
function AddOptions({ course, courses, target, onAdd }: {
  course: CourseData
  courses: CourseData[]
  target: ListType
  onAdd: (filter: CourseFilter) => void
}) {
  const sameName = courses.filter((c) => c.name === course.name)
  const sameProf = sameName.filter((c) => c.professor === course.professor)
  const targetLabel = target === 'required' ? '필수로 담기' : '희망으로 담기'

  if (sameName.length === 1) {
    return (
      <div className="animate-fade-in px-3 pb-3">
        <Button size="sm" variant="primary" onClick={() => onAdd({ name: course.name })}>
          {targetLabel}
        </Button>
      </div>
    )
  }

  const firstSlot = course.slots[0]
  const options: { label: string; detail: string; filter: CourseFilter }[] = [
    { label: '분반 상관없이', detail: `${sameName.length}개 중 시간표에 맞게`, filter: { name: course.name } },
    ...(course.professor && sameProf.length > 1 && sameProf.length < sameName.length
      ? [{ label: `${course.professor} 교수님 분반만`, detail: `${sameProf.length}개`, filter: { name: course.name, professor: course.professor } }]
      : []),
    {
      label: '이 분반만',
      detail: firstSlot ? `${firstSlot.day} ${firstSlot.start}${course.slots.length > 1 ? ' 외' : ''}` : `#${course.id}`,
      filter: { courseId: course.id, name: course.name },
    },
  ]

  return (
    <div className="animate-fade-in px-3 pb-3">
      <p className="mb-1 text-[12px] text-fg-muted">어떤 분반으로 {target === 'required' ? '필수' : '희망'}에 담을까요?</p>
      <div className="space-y-1">
        {options.map((o, i) => (
          <button
            key={o.label}
            type="button"
            onClick={() => onAdd(o.filter)}
            className={cx(
              'flex w-full items-center justify-between gap-3 rounded-md px-3 py-2 text-left transition active:scale-[0.99]',
              i === 0 ? 'bg-accent text-fg-on-accent hover:bg-accent-hover' : 'bg-surface-sunken hover:brightness-95',
            )}
          >
            <span className="text-[14px] font-medium">{o.label}</span>
            <span className={cx('shrink-0 text-[12px] tabular-nums', i === 0 ? 'opacity-85' : 'text-fg-muted')}>{o.detail}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

export function Dot({ tone }: { tone: ListType }) {
  return <span className={cx('size-1.5 shrink-0 rounded-full', tone === 'required' ? 'bg-required' : 'bg-desired')} />
}

import { Check, ChevronDown, Plus, Search, X } from 'lucide-react'
import { useDeferredValue, useMemo, useState } from 'react'
import { Badge, Button, cx, EmptyState, IconButton } from '../components/ui'
import { matchesFilter, timeSummary } from '../engine/course'
import { courseColorVars } from '../lib/courseColors'
import type { PreviewItem } from './Timetable'
import type { CourseData, CourseFilter } from '../engine/types'
import { useConfig, useStore, type ListType } from '../lib/store'

const PAGE = 40

function normalize(text: string) {
  return text.toLowerCase().replace(/\s+/g, '')
}

interface Group {
  name: string
  sections: CourseData[]
}

/**
 * 강의 검색 — 과목 단위로 한 줄, 펼치면 분반 목록
 * - ⊕: 과목 담기 (분반 상관없이) / 분반 옆 +: 이 분반만 담기
 * - 펼친 과목·누른 분반은 시간표에 점선으로 미리보기 (onPreview)
 */
export function SearchPanel({ courses, onPreview, pageScroll }: {
  courses: CourseData[]
  onPreview: (items: PreviewItem[] | null) => void
  /** 모바일: 목록이 따로 스크롤하지 않고 화면과 함께 스크롤, 검색창은 위에 고정 */
  pageScroll?: boolean
}) {
  const { dispatch } = useStore()
  const config = useConfig()
  const [query, setQuery] = useState('')
  const [limit, setLimit] = useState(PAGE)
  const [open, setOpen] = useState<{ name: string; sectionId: string | null } | null>(null)
  const deferredQuery = useDeferredValue(query)

  const groups = useMemo<Group[]>(() => {
    const keywords = deferredQuery.split(/\s+/).filter(Boolean).map(normalize)
    const matched = keywords.length
      ? courses.filter((c) => {
          const hay = normalize(`${c.name} ${c.professor} ${c.id}`)
          return keywords.every((k) => hay.includes(k))
        })
      : courses
    const byName = new Map<string, CourseData[]>()
    for (const c of matched) byName.set(c.name, [...(byName.get(c.name) ?? []), c])
    // 강의명이 검색어로 시작하는 과목 우선, 그다음 가나다
    const first = keywords[0]
    return [...byName.entries()]
      .map(([name, sections]) => ({ name, sections: sections.sort((a, b) => a.professor.localeCompare(b.professor, 'ko') || a.id.localeCompare(b.id)) }))
      .sort((a, b) => {
        if (first) {
          const sa = normalize(a.name).startsWith(first) ? 0 : 1
          const sb = normalize(b.name).startsWith(first) ? 0 : 1
          if (sa !== sb) return sa - sb
        }
        return a.name.localeCompare(b.name, 'ko')
      })
  }, [courses, deferredQuery])

  const membership = (sections: CourseData[]): ListType | null => {
    if (config.required.some((f) => sections.some((c) => matchesFilter(f, c)))) return 'required'
    if (config.desired.some((f) => sections.some((c) => matchesFilter(f, c)))) return 'desired'
    return null
  }

  /** 분반 상관없이 담기 / 이미 그렇게 담겼으면 뺌 */
  const isAny = (f: CourseFilter, name: string) => f.name === name && !f.courseId && !f.professor
  const anyAdded = (name: string) => [...config.required, ...config.desired].some((f) => isAny(f, name))
  const toggleAny = (name: string) => {
    if (anyAdded(name)) {
      dispatch({ type: 'setLists', required: config.required.filter((f) => !isAny(f, name)), desired: config.desired.filter((f) => !isAny(f, name)) })
    } else {
      dispatch({ type: 'addFilter', list: 'desired', filter: { name } })
    }
  }
  const sectionAdded = (c: CourseData) => [...config.required, ...config.desired].some((f) => f.courseId === c.id)

  /** 이 분반만 담기 / 이미 이 분반으로 담겼으면 뺌 */
  const toggleSection = (c: CourseData) => {
    const has = (list: ListType) => config[list].some((f) => f.courseId === c.id)
    if (has('required') || has('desired')) {
      const keep = (list: ListType) => config[list].filter((f) => f.courseId !== c.id)
      dispatch({ type: 'setLists', required: keep('required'), desired: keep('desired') })
    } else {
      dispatch({ type: 'addFilter', list: 'desired', filter: { courseId: c.id, name: c.name } })
    }
  }

  const expand = (g: Group) => {
    if (open?.name === g.name) {
      setOpen(null)
      onPreview(null)
    } else {
      setOpen({ name: g.name, sectionId: null })
      onPreview(g.sections.map((course, i) => ({ course, color: colorNo(i) })))
    }
  }
  const selectSection = (g: Group, c: CourseData, i: number) => {
    const same = open?.sectionId === c.id
    setOpen({ name: g.name, sectionId: same ? null : c.id })
    onPreview(same ? g.sections.map((course, k) => ({ course, color: colorNo(k) })) : [{ course: c, color: colorNo(i) }])
  }

  return (
    <div className={pageScroll ? undefined : 'flex h-full min-h-0 flex-col'}>
      <div className={cx('space-y-2 px-4 pt-1 pb-3', pageScroll && 'sticky top-0 z-10 bg-surface')}>
        <div className="relative">
          <Search size={16} className="pointer-events-none absolute top-1/2 left-2.5 -translate-y-1/2 text-fg-subtle" />
          <input
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
              setLimit(PAGE)
              // 검색어가 바뀌면 펼친 과목·미리보기도 닫음
              setOpen(null)
              onPreview(null)
            }}
            placeholder="강의명, 교수명, 강의번호"
            aria-label="강의 검색"
            className="h-9 w-full rounded-md bg-surface-sunken pr-9 pl-8 text-[15px] outline-none placeholder:text-fg-subtle focus:ring-2 focus:ring-accent-soft"
          />
          {query && (
            <IconButton label="검색어 지우기" size="sm" className="absolute top-1/2 right-1 size-6 -translate-y-1/2" onClick={() => setQuery('')}>
              <X size={13} />
            </IconButton>
          )}
        </div>
        <p className="px-0.5 text-[12px] text-fg-muted tabular-nums">
          {groups.length.toLocaleString()}개 과목
        </p>
      </div>

      <div className={cx('px-2 pb-4', !pageScroll && 'min-h-0 flex-1 overflow-y-auto')}>
        {groups.length === 0 ? (
          <EmptyState icon={<Search size={36} strokeWidth={1.5} />} title="검색 결과 없음" />
        ) : (
          <ul>
            {groups.slice(0, limit).map((g) => {
              const member = membership(g.sections)
              const isOpen = open?.name === g.name
              const credits = [...new Set(g.sections.map((c) => c.credits))].join('/')
              const profs = [...new Set(g.sections.map((c) => c.professor).filter(Boolean))]
              return (
                <li key={g.name} className={cx('rounded-md transition-colors', isOpen ? 'bg-surface-raised shadow-sm' : 'hover:bg-surface-hover')}>
                  <div className="py-2 pr-3 pl-3">
                    <button type="button" onClick={() => expand(g)} aria-expanded={isOpen} className="flex w-full min-w-0 items-center gap-2 text-left">
                      <span className="min-w-0 flex-1">
                        <span className="flex flex-wrap items-center gap-x-1.5 gap-y-0.5">
                          <span className="min-w-0 text-[15px] leading-snug font-semibold tracking-tight break-keep [overflow-wrap:anywhere]">{g.name}</span>
                          {member && <Badge tone={member === 'required' ? 'accent' : 'neutral'}>{member === 'required' ? '필수' : '희망'}</Badge>}
                        </span>
                        <span className="mt-0.5 block truncate text-[13px] text-fg-muted">
                          {g.sections.length > 1 ? `분반 ${g.sections.length}개` : timeSummary(g.sections[0])} · {credits}학점
                          {profs.length > 0 && ` · ${profs.slice(0, 2).join(', ')}${profs.length > 2 ? ` 외 ${profs.length - 2}명` : ''}`}
                        </span>
                      </span>
                      <ChevronDown size={15} className={cx('shrink-0 text-fg-subtle transition-transform', isOpen && 'rotate-180')} />
                    </button>
                  </div>

                  {isOpen && (
                    <ul className="animate-fade-in px-1.5 pb-1.5">
                      {g.sections.length > 1 && (
                        <li className="flex items-center gap-1 rounded-md transition-colors hover:bg-surface-hover">
                          <span className="min-w-0 flex-1 py-2 pr-1 pl-2.5">
                            <span className="block text-[13px] font-medium">분반 상관없이</span>
                            <span className="block text-[12px] text-fg-muted">시간표에 맞는 분반으로 자동</span>
                          </span>
                          <AddToggle added={anyAdded(g.name)} label="분반 상관없이 담기" onClick={() => toggleAny(g.name)} />
                        </li>
                      )}
                      {g.sections.map((c, i) => {
                        const selected = open?.sectionId === c.id
                        // 분반이 하나뿐이면 이 줄의 + 가 곧 과목 담기 (분반 상관없이)
                        const single = g.sections.length === 1
                        const added = single ? anyAdded(g.name) || sectionAdded(c) : sectionAdded(c)
                        // '분반 상관없이'로 담았으면 모든 분반이 포함된 것 → 같이 체크 (따로 빼거나 담을 수는 없음)
                        const implied = !single && !added && anyAdded(g.name)
                        const toggle = () => (single && !sectionAdded(c) ? toggleAny(g.name) : toggleSection(c))
                        return (
                          <li key={c.id} className={cx('flex items-center gap-1 rounded-md transition-colors', selected ? 'bg-surface-sunken' : 'hover:bg-surface-hover')}>
                            <button type="button" onClick={() => selectSection(g, c, i)} aria-pressed={selected} className="flex min-w-0 flex-1 items-center gap-2.5 py-2 pr-1 pl-2.5 text-left">
                              {/* 시간표 미리보기와 같은 색 */}
                              <span className="size-2.5 shrink-0 rounded-full" style={{ background: courseColorVars(colorNo(i)).bar }} />
                              <span className="min-w-0 flex-1">
                                <span className="block truncate text-[13px] tabular-nums">{timeSummary(c)}</span>
                                <span className="block truncate text-[12px] text-fg-muted">
                                  {c.professor || '교수 미정'} · #{c.id}
                                  {c.slots[0]?.room && ` · ${c.slots[0].room}`}
                                </span>
                              </span>
                            </button>
                            <AddToggle added={added} implied={implied} label={single ? '담기' : '이 분반만 담기'} onClick={toggle} />
                          </li>
                        )
                      })}
                    </ul>
                  )}
                </li>
              )
            })}
          </ul>
        )}
        {groups.length > limit && (
          <div className="flex justify-center pt-3">
            <Button variant="secondary" size="sm" onClick={() => setLimit((l) => l + PAGE)}>
              더 보기
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

const colorNo = (i: number) => (i % 10) + 1

/** 담기(+) / 담김(✓) 토글 — 담긴 상태는 강조색, '분반 상관없이'에 포함된 분반은 연한 체크(누를 수 없음) */
function AddToggle({ added, implied, label, onClick }: { added: boolean; implied?: boolean; label: string; onClick: () => void }) {
  return (
    <IconButton
      label={added ? '빼기' : implied ? '분반 상관없이로 담겨 있음' : label}
      size="sm"
      disabled={implied}
      className={cx(
        'mr-1',
        added && 'bg-accent text-fg-on-accent hover:bg-accent-hover hover:text-fg-on-accent',
        // disabled 의 흐림(opacity) 대신 연한 강조색으로 '포함됨'을 보여 줌
        implied && 'bg-accent-soft text-accent-fg disabled:opacity-100',
      )}
      onClick={onClick}
    >
      {added || implied ? <Check size={14} strokeWidth={2.8} /> : <Plus size={15} strokeWidth={2.4} />}
    </IconButton>
  )
}

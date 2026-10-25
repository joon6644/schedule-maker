import { Pin } from 'lucide-react'
import { useMemo } from 'react'
import { cx } from '../components/ui'
import { toMinutes } from '../engine/course'
import { WEEKDAYS, type CourseData, type Day, type ExcludedTime } from '../engine/types'
import { courseColorVars } from '../lib/courseColors'

const HOUR = 'var(--timetable-hour-height)'

export interface PreviewItem {
  course: CourseData
  /** 팔레트 번호 (--color-course-N-*) */
  color: number
}

/**
 * Apple Calendar 스타일 주간 시간표
 * 시간·요일마다 희미한 격자 + 강의 블록(연한 시스템 색 틴트)
 * avoid 를 넘기면 피하고 싶은 시간(공강 요일 포함)을 빗금으로 표시
 */
export function Timetable({
  courses,
  colors,
  avoid,
  preview,
  pinned,
  onCourseClick,
}: {
  courses: CourseData[]
  colors: Map<string, number>
  avoid?: { days: Day[]; times: ExcludedTime[] }
  /** 강의 검색에서 펼친 과목·분반 미리보기 (분반마다 색 번호) */
  preview?: PreviewItem[]
  pinned: Set<string>
  onCourseClick?: (course: CourseData) => void
}) {
  const { days, startHour, endHour } = useMemo(() => {
    const slots = [...courses, ...(preview ?? []).map((p) => p.course)].flatMap((c) => c.slots)
    const hasSat = slots.some((s) => s.day === '토')
    const minStart = Math.min(9 * 60, ...slots.map((s) => toMinutes(s.start)))
    const maxEnd = Math.max(18 * 60, ...slots.map((s) => toMinutes(s.end)))
    return {
      days: hasSat ? ([...WEEKDAYS, '토'] as Day[]) : WEEKDAYS,
      startHour: Math.floor(minStart / 60),
      endHour: Math.ceil(maxEnd / 60),
    }
  }, [courses, preview])

  const hours = Array.from({ length: endHour - startHour }, (_, i) => startHour + i)
  const previewing = !!preview?.length
  const clampTime = (time: string) => Math.min(Math.max(toMinutes(time), startHour * 60), endHour * 60)
  const top = (time: string) => `calc(${(clampTime(time) - startHour * 60) / 60} * ${HOUR})`
  const height = (start: string, end: string) => `calc(${(clampTime(end) - clampTime(start)) / 60} * ${HOUR})`
  const columns = `40px repeat(${days.length}, minmax(0, 1fr))`
  const bodyHeight = `calc(${hours.length} * ${HOUR})`

  return (
    <div>
      {/* 요일 헤더 */}
      <div className="grid pb-2" style={{ gridTemplateColumns: columns }}>
        <div />
        {/* 틀은 조건과 상관없이 항상 같은 모양 */}
        {days.map((d) => (
          <div key={d} className="text-center text-[13px] font-semibold text-fg-muted">
            {d}
          </div>
        ))}
      </div>

      <div className="grid" style={{ gridTemplateColumns: columns }}>
        {/* 시간 눈금: 격자선 높이에 맞춰 라벨 배치 */}
        <div className="relative" style={{ height: bodyHeight }}>
          {hours.map((h, i) => (
            <span
              key={h}
              className="absolute right-2 -translate-y-1/2 text-[11px] leading-none text-fg-subtle tabular-nums"
              style={{ top: `calc(${i} * ${HOUR})` }}
            >
              {h}시
            </span>
          ))}
        </div>

        {days.map((day) => (
          <div
            key={day}
            className="relative border-b border-l border-grid last:border-r"
            style={{
              height: bodyHeight,
              // 1시간마다 희미한 가로선
              backgroundImage: 'linear-gradient(to bottom, var(--color-grid) 1px, transparent 1px)',
              backgroundSize: `100% ${HOUR}`,
            }}
          >
            {/* 피하고 싶은 시간 (표시를 켠 경우) */}
            {avoid?.days.includes(day) && <div className="hatch absolute inset-0" />}
            {avoid?.times
              .filter((t) => t.day === day)
              .map((t) => (
                <div
                  key={`${t.start}-${t.end}`}
                  className="hatch absolute inset-x-0"
                  style={{ top: top(t.start), height: height(t.start, t.end) }}
                  title={`피하고 싶은 시간 ${t.start}–${t.end}`}
                />
              ))}

            {/* 미리보기 (강의 블록 위에 겹쳐서, 클릭은 통과) */}
            {preview?.flatMap(({ course, color: colorNo }) =>
              course.slots
                .filter((s) => s.day === day)
                .map((s) => {
                  // 분반마다 다른 색 → 월·수처럼 나뉜 블록도 같은 분반끼리 같은 색 (검색 목록의 점과 같은 색)
                  const color = courseColorVars(colorNo)
                  return (
                    <div
                      key={`preview-${course.id}-${s.start}`}
                      className="animate-fade-in pointer-events-none absolute inset-x-[2px] z-10 overflow-hidden rounded-[2px] px-1.5 pt-1 shadow-md ring-1 ring-inset sm:px-2 sm:pt-1.5"
                      // 일반 강의 블록과 같은 모양 + 얇은 실선 테두리 (불투명 면: 아래 글자가 비치지 않게)
                      style={{
                        top: `calc(${top(s.start)} + 1px)`,
                        height: `calc(${height(s.start, s.end)} - 2px)`,
                        background: color.bg,
                        color: color.fg,
                        ['--tw-ring-color' as string]: color.bar,
                      }}
                    >
                      <span className="block text-[11px] leading-[1.2] font-semibold break-keep [overflow-wrap:anywhere] sm:text-[12px]">{course.name}</span>
                      <span className="block truncate text-[10px] leading-[1.2] opacity-75 sm:text-[11px]">
                        {[s.room, course.professor].filter(Boolean).join(' · ')}
                      </span>
                    </div>
                  )
                }),
            )}

            {/* 강의 블록 */}
            {courses.flatMap((course) =>
              course.slots
                .filter((s) => s.day === day)
                .map((s) => {
                  const color = courseColorVars(colors.get(course.name) ?? 1)
                  const isPinned = pinned.has(course.name)
                  // 과목명은 자르지 않고 전부 보여줌. 강의실·교수도 항상 보여주되,
                  // 이름이 길고 짧은 수업은 좁은 화면(모바일)에서만 숨김
                  const minutes = toMinutes(s.end) - toMinutes(s.start)
                  const short = minutes < 60
                  const longName = course.name.length > 10
                  const metaClass = longName && minutes < 75 ? 'hidden sm:block' : 'block'
                  return (
                    <button
                      key={`${course.id}-${s.start}`}
                      type="button"
                      onClick={() => onCourseClick?.(course)}
                      className={cx(
                        // 각진 블록: 시간표다운 정돈된 인상
                        'group animate-fade-in absolute inset-x-[2px] overflow-hidden rounded-[2px] text-left transition hover:brightness-[0.97] active:scale-[0.98]',
                        // 미리보기 중에는 원래 시간표를 희미하게
                        // (opacity 대신 filter: 페이드인 애니메이션의 opacity 에 덮이지 않도록)
                        previewing && '[filter:opacity(0.3)_saturate(0.6)]',
                        isPinned && 'ring-2 ring-inset',
                      )}
                      style={{
                        top: `calc(${top(s.start)} + 1px)`,
                        height: `calc(${height(s.start, s.end)} - 2px)`,
                        background: color.bg,
                        color: color.fg,
                        ['--tw-ring-color' as string]: color.bar,
                      }}
                      title={`${course.name} · ${course.professor} · ${s.start}~${s.end}${s.room ? ` · ${s.room}` : ''}
${isPinned ? '눌러서 고정 해제' : '눌러서 고정'}`}
                    >
                      {/* 마우스를 올리면 고정할 수 있다는 표시 */}
                      {!isPinned && onCourseClick && (
                        <Pin size={11} className="absolute top-1 right-1 opacity-0 transition-opacity group-hover:opacity-60 group-focus-visible:opacity-60" />
                      )}
                      <span className={cx('block px-1.5 sm:px-2', short ? 'pt-0.5 sm:pt-1' : 'pt-1 sm:pt-1.5')}>
                        <span className="flex items-start gap-1">
                          {/* 단어 단위로 줄바꿈하되, 띄어쓰기 없는 긴 과목명은 글자 단위로 넘김 */}
                          <span
                            className={cx(
                              'min-w-0 leading-[1.2] font-semibold break-keep [overflow-wrap:anywhere]',
                              longName ? 'text-[10px] sm:text-[11px]' : 'text-[11px] sm:text-[12px]',
                            )}
                          >
                            {course.name}
                          </span>
                          {isPinned && <Pin size={11} className="mt-px shrink-0" fill="currentColor" />}
                        </span>
                        <span className={cx('truncate text-[10px] leading-[1.2] opacity-75 sm:text-[11px]', short ? 'mt-0' : 'mt-0.5', metaClass)}>
                          {[s.room, course.professor].filter(Boolean).join(' · ')}
                        </span>
                      </span>
                    </button>
                  )
                }),
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

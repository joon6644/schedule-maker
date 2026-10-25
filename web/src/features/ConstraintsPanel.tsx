import { useState } from 'react'
import { AddRow, Button, cx, ListRow, RemoveButton, Section, Segmented, Stepper, Switch } from '../components/ui'
import { toMinutes } from '../engine/course'
import { CLASS_DAYS, type Day, type ExcludedTime } from '../engine/types'
import { useConfig, useStore } from '../lib/store'

/** 시간을 지정할 때만 보여주는 빠른 입력 (기본 설정이 아니라 입력 도우미) */
const SUGGESTIONS = [
  { label: '1교시', start: '09:00', end: '10:00' },
  { label: '점심', start: '12:00', end: '13:00' },
  { label: '저녁', start: '18:00', end: '23:00' },
]

const same = (t: ExcludedTime, start: string, end: string) => t.start === start && t.end === end
const dayLabel = (days: Day[]) => ({ 월화수목금: '월–금', 월화수목금토: '월–토' })[days.join('')] ?? days.join(' · ')
const timeLabel = (start: string, end: string) => (end >= '23:00' ? `${start} 이후` : `${start}–${end}`)

export function ConstraintsPanel() {
  const { state, dispatch } = useStore()
  const config = useConfig()
  const hasAvoid = config.excludedDays.length > 0 || config.excludedTimes.length > 0
  const setCredits = (min: number, max: number) => dispatch({ type: 'setCredits', min, max: Math.max(min, max) })

  return (
    <div className="space-y-7 px-4 pt-1 pb-6">
      <Section title="이수 학점" flush>
        <ListRow label="최소">
          <Stepper label="최소 학점" value={config.minCredits} min={1} max={30} onChange={(v) => setCredits(v, config.maxCredits)} />
        </ListRow>
        <ListRow label="최대">
          <Stepper label="최대 학점" value={config.maxCredits} min={config.minCredits} max={30} onChange={(v) => setCredits(config.minCredits, v)} />
        </ListRow>
      </Section>

      <AvoidTimes />

      {/* 조건이 아니라 보기 옵션이라 따로 묶음 */}
      {hasAvoid && (
        <Section title="시간표 보기" flush>
          <ListRow label="피하고 싶은 시간 빗금 표시">
            <Switch label="피하고 싶은 시간 빗금 표시" checked={state.showAvoid} onChange={(show) => dispatch({ type: 'setShowAvoid', show })} />
          </ListRow>
        </Section>
      )}
    </div>
  )
}

/** 공강 요일(하루 종일)과 피하고 싶은 시간대를 한 목록에서 관리 */
function AvoidTimes() {
  const { dispatch } = useStore()
  const config = useConfig()
  const times = config.excludedTimes
  const [open, setOpen] = useState(false)

  // 같은 시간대끼리 묶어 한 줄로
  const groups = [...new Map(times.map((t) => [`${t.start}-${t.end}`, { start: t.start, end: t.end }])).values()]
    .map((g) => ({ ...g, days: CLASS_DAYS.filter((d) => times.some((t) => t.day === d && same(t, g.start, g.end))) }))
    .sort((a, b) => toMinutes(a.start) - toMinutes(b.start))
  const allDay = CLASS_DAYS.filter((d) => config.excludedDays.includes(d))
  const empty = allDay.length === 0 && groups.length === 0

  return (
    <Section title="피하고 싶은 시간" flush>
      {empty && !open && <p className="px-4 py-3 text-[15px] text-fg-subtle">없음</p>}

      {allDay.length > 0 && (
        <Row
          days={allDay}
          detail="하루 종일"
          onRemove={() => allDay.forEach((day) => dispatch({ type: 'toggleDay', day }))}
        />
      )}
      {groups.map((g) => (
        <Row
          key={`${g.start}-${g.end}`}
          days={g.days}
          detail={timeLabel(g.start, g.end)}
          onRemove={() => dispatch({ type: 'setExcludedTimes', times: times.filter((t) => !same(t, g.start, g.end)) })}
        />
      ))}

      {open ? (
        <Editor onClose={() => setOpen(false)} />
      ) : (
        <AddRow label="추가" onClick={() => setOpen(true)} />
      )}
    </Section>
  )
}

function Row({ days, detail, onRemove }: { days: Day[]; detail: string; onRemove: () => void }) {
  return (
    <div className="flex min-h-11 items-center gap-3 py-1 pr-2 pl-4">
      <span className="flex-1 text-[15px]">{dayLabel(days)}</span>
      <span className="text-[15px] text-fg-muted tabular-nums">{detail}</span>
      <RemoveButton onClick={onRemove} />
    </div>
  )
}

function Editor({ onClose }: { onClose: () => void }) {
  const { dispatch } = useStore()
  const config = useConfig()
  const [days, setDays] = useState<Day[]>([])
  const [mode, setMode] = useState<'time' | 'allDay'>('time')
  const [start, setStart] = useState('09:00')
  const [end, setEnd] = useState('10:30')
  const badRange = mode === 'time' && toMinutes(end) <= toMinutes(start)

  const add = () => {
    if (mode === 'allDay') days.filter((d) => !config.excludedDays.includes(d)).forEach((day) => dispatch({ type: 'toggleDay', day }))
    else days.forEach((day) => dispatch({ type: 'addExcludedTime', time: { day, start, end } }))
    onClose()
  }

  return (
    <div className="animate-fade-in space-y-3 px-4 pt-2 pb-3">
      <div className="grid grid-cols-6 gap-1.5">
        {CLASS_DAYS.map((d) => {
          const on = days.includes(d)
          return (
            <button
              key={d}
              type="button"
              aria-pressed={on}
              onClick={() => setDays((prev) => (prev.includes(d) ? prev.filter((x) => x !== d) : CLASS_DAYS.filter((x) => x === d || prev.includes(x))))}
              className={cx('h-9 rounded-full text-[15px] font-medium transition active:scale-95', on ? 'bg-accent text-fg-on-accent' : 'bg-surface-sunken text-fg')}
            >
              {d}
            </button>
          )
        })}
      </div>

      <Segmented
        size="sm"
        value={mode}
        onChange={setMode}
        options={[
          { value: 'time', label: '시간 지정' },
          { value: 'allDay', label: '하루 종일' },
        ]}
      />

      {mode === 'time' && (
        <>
          <div className="flex items-center gap-2">
            <TimeInput value={start} onChange={setStart} label="시작 시간" />
            <span className="text-fg-subtle">–</span>
            <TimeInput value={end} onChange={setEnd} label="종료 시간" />
          </div>
          <div className="flex flex-wrap items-center gap-1">
            {SUGGESTIONS.map((s) => (
              <button
                key={s.label}
                type="button"
                onClick={() => {
                  setStart(s.start)
                  setEnd(s.end)
                }}
                className={cx(
                  'rounded-full px-2.5 py-1 text-[12px] transition',
                  start === s.start && end === s.end ? 'bg-accent-soft text-accent-fg' : 'text-fg-muted hover:bg-surface-hover',
                )}
              >
                {s.label} {timeLabel(s.start, s.end)}
              </button>
            ))}
          </div>
          {badRange && <p className="text-[12px] text-danger">끝나는 시간이 시작 시간보다 늦어야 해요.</p>}
        </>
      )}

      <div className="flex justify-end gap-1.5">
        <Button variant="ghost" size="sm" onClick={onClose}>
          취소
        </Button>
        <Button variant="primary" size="sm" disabled={days.length === 0 || badRange} onClick={add}>
          {days.length === 0 ? '요일을 고르세요' : '추가'}
        </Button>
      </div>
    </div>
  )
}

function TimeInput({ value, onChange, label }: { value: string; onChange: (v: string) => void; label: string }) {
  return (
    <input
      type="time"
      step={300}
      value={value}
      aria-label={label}
      onChange={(e) => e.target.value && onChange(e.target.value)}
      className="h-9 min-w-0 flex-1 rounded-sm bg-surface-sunken px-2.5 text-[15px] tabular-nums outline-none focus:ring-2 focus:ring-accent-soft"
    />
  )
}

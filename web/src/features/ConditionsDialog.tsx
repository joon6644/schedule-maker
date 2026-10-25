import { Check, FolderOpen } from 'lucide-react'
import { useState } from 'react'
import { AddRow, Button, ConfirmDialog, Dialog, IconButton, NameForm, nextName, Section, type ToastData } from '../components/ui'
import { CLASS_DAYS, type ScheduleConfig } from '../engine/types'
import { useConfig, usePresets, useStore, type ConditionPreset } from '../lib/store'
import { SavedRow } from './SavedPanel'

type Notify = (message: string, action?: ToastData['action']) => void

/**
 * 맨 위 '저장·불러오기' 버튼 + 대화상자
 * 조건 = 담은 강의 + 학점·공강·피하고 싶은 시간 한 묶음 (이 브라우저에 학기별 보관)
 */
export function ConditionsButton({ notify, onApplied }: { notify: Notify; onApplied: () => void }) {
  const [open, setOpen] = useState(false)
  return (
    <>
      {/* Button 의 inline-flex 와 겹치지 않도록 반응형 표시는 감싸는 요소에서 처리 */}
      <span className="hidden md:flex">
        <Button variant="ghost" size="sm" onClick={() => setOpen(true)}>
          <FolderOpen size={15} /> 저장·불러오기
        </Button>
      </span>
      <span className="flex md:hidden">
        <IconButton label="저장·불러오기" onClick={() => setOpen(true)}>
          <FolderOpen size={17} />
        </IconButton>
      </span>
      <Dialog open={open} onClose={() => setOpen(false)} title="조건 저장·불러오기">
        <SavedConditions
          notify={notify}
          onDone={() => {
            setOpen(false)
            onApplied()
          }}
        />
      </Dialog>
    </>
  )
}

function SavedConditions({ onDone, notify }: { onDone: () => void; notify: Notify }) {
  const presets = usePresets()
  const config = useConfig()
  const { dispatch } = useStore()
  const [adding, setAdding] = useState(false)
  /** 지금 조건과 똑같이 저장된 것이 있으면 저장을 막고 알려 줌 */
  const [duplicate, setDuplicate] = useState<ConditionPreset | null>(null)
  const startSave = () => {
    const same = presets.find((p) => sameConfig(p.config, config))
    if (same) setDuplicate(same)
    else setAdding(true)
  }
  /** 불러오기 전에 확인 중인 조건 */
  const [confirming, setConfirming] = useState<ConditionPreset | null>(null)

  const save = (name: string) => {
    dispatch({ type: 'savePreset', preset: { id: `${Date.now()}`, name, config } })
    notify(`'${name}' 저장함`)
    setAdding(false)
    onDone()
  }
  // 불러오면 담은 강의·조건이 통째로 바뀜 → 바뀐 결과 알림에서 되돌리기 (App 의 변화 알림)
  const apply = (p: ConditionPreset) => {
    dispatch({ type: 'replaceConfig', config: p.config })
    onDone()
  }
  const remove = (p: ConditionPreset) => {
    dispatch({ type: 'removePreset', id: p.id })
    notify(`'${p.name}' 삭제함`, { label: '되돌리기', onClick: () => dispatch({ type: 'savePreset', preset: p }) })
  }

  return (
    <div className="space-y-6">
      <Section flush>
        {adding ? (
          <div className="px-4 pt-2 pb-3">
            <NameForm
              initial={nextName('조건', presets.map((p) => p.name))}
              taken={(name) => presets.some((p) => p.name === name)}
              onSubmit={save}
              onCancel={() => setAdding(false)}
            />
          </div>
        ) : duplicate && presets.some((p) => p.id === duplicate.id) ? (
          <p className="flex min-h-11 items-center px-4 text-[15px] text-fg-muted">
            이미 저장된 ‘{duplicate.name}’{withGwa(duplicate.name)} 동일합니다
          </p>
        ) : (
          <AddRow label="지금 조건 저장" onClick={startSave} />
        )}
      </Section>

      <Section title="저장한 조건" flush>
        {presets.length === 0 && <p className="px-4 py-3 text-[15px] text-fg-subtle">없음</p>}
        {presets.map((p) => {
          const applied = sameConfig(p.config, config)
          return (
            <SavedRow
              key={p.id}
              name={p.name}
              detail={summarize(p.config)}
              active={applied}
              activeMark={<Check size={14} strokeWidth={2.6} className="shrink-0 text-accent-fg" />}
              onClick={() => !applied && setConfirming(p)}
              onRename={(name) => dispatch({ type: 'renamePreset', id: p.id, name })}
              onRemove={() => remove(p)}
            />
          )
        })}
      </Section>

      {/* 불러오기 전 작은 확인 팝업: 지금 담은 강의·조건이 통째로 바뀌므로 */}
      <ConfirmDialog
        open={!!confirming}
        title={confirming && `‘${confirming.name}’${withRo(confirming.name)} 불러옵니다`}
        detail={confirming && summarize(confirming.config)}
        confirmLabel="불러오기"
        onConfirm={() => confirming && apply(confirming)}
        onCancel={() => setConfirming(null)}
      />
    </div>
  )
}

/** '조건 1'로 / '조건 3'으로 — 마지막 글자 받침에 맞춘 조사 (숫자는 읽는 소리 기준) */
function withRo(name: string) {
  const b = batchim(name)
  return b === 'none' || b === 'rieul' ? '로' : '으로'
}

/** '조건 1'과 / '조건 2'와 */
function withGwa(name: string) {
  return batchim(name) === 'none' ? '와' : '과'
}

/** 마지막 글자의 받침 — 숫자는 읽는 소리(영·일·이·삼…) 기준, 한글이 아니면 받침 없음으로 */
function batchim(name: string): 'none' | 'rieul' | 'other' {
  const last = name.trim().slice(-1)
  if (/[0-9]/.test(last)) return '036'.includes(last) ? 'other' : '178'.includes(last) ? 'rieul' : 'none'
  const code = last.charCodeAt(0) - 0xac00
  if (code < 0 || code > 11171) return 'none'
  const final = code % 28
  return final === 0 ? 'none' : final === 8 ? 'rieul' : 'other'
}

/** 담은 강의 수 + 학점 + 공강 + 피하고 싶은 시간 */
function summarize(c: ScheduleConfig) {
  const allDay = CLASS_DAYS.filter((d) => c.excludedDays.includes(d))
  return [
    c.required.length > 0 && `필수 ${c.required.length}`,
    c.desired.length > 0 && `희망 ${c.desired.length}`,
    `${c.minCredits}–${c.maxCredits}학점`,
    allDay.length > 0 && `${allDay.join('·')} 공강`,
    c.excludedTimes.length > 0 && `피하는 시간 ${new Set(c.excludedTimes.map((t) => `${t.start}-${t.end}`)).size}개`,
  ]
    .filter(Boolean)
    .join(' · ')
}

/** 담은 순서·요일 순서와 상관없이 같은 조건인지 */
function sameConfig(a: ScheduleConfig, b: ScheduleConfig) {
  const key = (c: ScheduleConfig) =>
    JSON.stringify([
      c.minCredits,
      c.maxCredits,
      c.required.map((f) => JSON.stringify(f)).sort(),
      c.desired.map((f) => JSON.stringify(f)).sort(),
      [...c.excludedDays].sort(),
      c.excludedTimes.map((t) => `${t.day} ${t.start}-${t.end}`).sort(),
    ])
  return key(a) === key(b)
}


/**
 * 기본 UI 컴포넌트 — 새 화면은 먼저 여기 있는 컴포넌트를 조합한다
 *
 * Apple 스타일 원칙: 테두리·구분선 없음, 캡슐 버튼, 채워진(fill) 입력 컨트롤, 그룹은 배경 대비로만 구분
 */
import { Minus, Plus, X } from 'lucide-react'
import { useEffect, useRef, useState, type ButtonHTMLAttributes, type ReactNode } from 'react'
import { createPortal } from 'react-dom'

export function cx(...classes: (string | false | null | undefined)[]) {
  return classes.filter(Boolean).join(' ')
}

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'
type ButtonSize = 'sm' | 'md'

/**
 * 버튼 위계 (Material 3 / Apple HIG): 한 영역에 primary 는 하나만
 * - primary: 가장 중요한 동작 (강조색 채움)
 * - secondary: 그 밖의 동작 (중립 회색 채움)
 * - ghost: 보조·취소·링크성 동작 (글자만)
 */
const buttonVariants: Record<ButtonVariant, string> = {
  primary: 'bg-accent text-fg-on-accent hover:bg-accent-hover',
  secondary: 'bg-surface-sunken text-fg hover:brightness-95',
  ghost: 'text-accent-fg hover:bg-surface-hover',
  danger: 'text-danger hover:bg-danger-soft',
}
const buttonSizes: Record<ButtonSize, string> = {
  sm: 'h-7 px-3 text-[13px] gap-1',
  md: 'h-9 px-4 text-[15px] gap-1.5',
}

export function Button({
  variant = 'secondary',
  size = 'md',
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant; size?: ButtonSize }) {
  return (
    <button
      type="button"
      className={cx(
        'inline-flex shrink-0 items-center justify-center rounded-full font-medium whitespace-nowrap transition active:scale-[0.97] disabled:pointer-events-none disabled:opacity-35',
        buttonVariants[variant],
        buttonSizes[size],
        className,
      )}
      {...props}
    />
  )
}

export function IconButton({
  label,
  size = 'md',
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { label: string; size?: 'sm' | 'md' }) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      className={cx(
        'inline-flex shrink-0 items-center justify-center rounded-full text-fg-muted transition hover:bg-surface-hover hover:text-fg active:scale-95 disabled:pointer-events-none disabled:opacity-30',
        size === 'sm' ? 'size-7' : 'size-9',
        className,
      )}
      {...props}
    />
  )
}

/** 배지는 세 가지만: 중립(기본) · 강조(필수처럼 중요한 것 하나) · 경고 */
type BadgeTone = 'neutral' | 'accent' | 'warning'
const badgeTones: Record<BadgeTone, string> = {
  neutral: 'bg-surface-sunken text-fg-muted',
  accent: 'bg-accent-soft text-accent-fg',
  warning: 'bg-warning-soft text-warning',
}

export function Badge({ tone = 'neutral', children, className }: { tone?: BadgeTone; children: ReactNode; className?: string }) {
  return (
    <span className={cx('inline-flex h-[18px] items-center gap-0.5 rounded-full px-1.5 text-[11px] font-semibold whitespace-nowrap', badgeTones[tone], className)}>
      {children}
    </span>
  )
}

/** iOS UISegmentedControl */
export function Segmented<T extends string>({
  value,
  options,
  onChange,
  className,
  size = 'md',
}: {
  value: T
  options: { value: T; label: ReactNode }[]
  onChange: (value: T) => void
  className?: string
  size?: 'sm' | 'md'
}) {
  return (
    <div role="tablist" className={cx('flex rounded-[9px] bg-surface-sunken p-[2px]', className)}>
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          role="tab"
          aria-selected={o.value === value}
          onClick={() => onChange(o.value)}
          className={cx(
            'flex flex-1 items-center justify-center gap-1.5 rounded-[7px] font-medium whitespace-nowrap transition-all duration-200',
            size === 'sm' ? 'h-[26px] px-2.5 text-[12px]' : 'h-8 px-3 text-[13px]',
            o.value === value ? 'bg-thumb text-fg shadow-md' : 'text-fg-muted hover:text-fg',
          )}
        >
          {o.label}
        </button>
      ))}
    </div>
  )
}

/** iOS 설정 앱의 inset grouped 섹션: 머리글(밖) + 둥근 그룹 + 바닥글(밖) */
export function Section({ title, footer, action, children, className, flush }: {
  title?: ReactNode
  footer?: ReactNode
  action?: ReactNode
  children: ReactNode
  className?: string
  /** 리스트 행(ListRow)을 담을 때: 안쪽 여백 없이 */
  flush?: boolean
}) {
  return (
    <section className={className}>
      {(title || action) && (
        <header className="flex items-end justify-between gap-3 px-4 pb-1.5">
          {title && <h3 className="text-[13px] font-medium text-fg-muted">{title}</h3>}
          {action}
        </header>
      )}
      <div className={cx('rounded-lg bg-surface-raised', flush ? 'py-1' : 'p-4')}>{children}</div>
      {footer && <p className="px-4 pt-1.5 text-[12px] leading-relaxed text-fg-muted">{footer}</p>}
    </section>
  )
}

export interface ToastData {
  id: number
  message: ReactNode
  action?: { label: string; onClick: () => void }
}

/** 화면 아래 떠 있는 캡슐 알림 (선택적으로 '되돌리기' 같은 동작 하나) */
export function Toast({ toast, onClose, className }: { toast: ToastData | null; onClose: () => void; className?: string }) {
  if (!toast) return null
  return (
    <div
      key={toast.id}
      role="status"
      aria-live="polite"
      className={cx(
        // 좌우 16px 안에서 가운데 정렬 (left-1/2 기준이면 좁은 화면에서 폭이 절반으로 줄어듦)
        'animate-fade-in fixed inset-x-4 z-50 mx-auto flex w-fit max-w-xl items-center gap-2 rounded-[22px] bg-fg py-1.5 pr-1.5 pl-4 text-[13px] leading-snug font-medium text-bg shadow-lg',
        className,
      )}
    >
      <span className="min-w-0 py-1">{toast.message}</span>
      {toast.action && (
        <button
          type="button"
          onClick={() => {
            toast.action!.onClick()
            onClose()
          }}
          className="shrink-0 rounded-full bg-bg/15 px-3 py-1 font-semibold text-bg transition hover:bg-bg/25"
        >
          {toast.action.label}
        </button>
      )}
    </div>
  )
}

/** 목록 행의 삭제: 평소엔 회색, 가리키면 빨강 (빨간 동그라미를 늘어놓지 않음) */
export function RemoveButton({ label = '삭제', onClick }: { label?: string; onClick: () => void }) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      onClick={onClick}
      onPointerDown={(e) => e.stopPropagation()}
      onMouseDown={(e) => e.stopPropagation()}
      onTouchStart={(e) => e.stopPropagation()}
      className="flex size-7 shrink-0 items-center justify-center rounded-full text-fg-subtle transition hover:bg-danger-soft hover:text-danger active:scale-90"
    >
      <X size={15} strokeWidth={2.2} />
    </button>
  )
}

/** 목록 끝의 '+ 추가' 행 (강조색 글자) */
export function AddRow({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex min-h-11 w-full items-center gap-2 px-4 text-left text-[15px] font-medium text-accent-fg transition hover:bg-surface-hover active:opacity-60"
    >
      <Plus size={17} strokeWidth={2.2} />
      {label}
    </button>
  )
}

/** 버튼 아래 떠서 열리는 작은 창 — 바깥을 누르거나 Esc 면 닫힘 (주변 레이아웃을 밀지 않음) */
export function Popover({ open, onClose, trigger, children, className }: {
  open: boolean
  onClose: () => void
  trigger: ReactNode
  children: ReactNode
  className?: string
}) {
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!open) return
    const onDown = (e: MouseEvent) => {
      if (!ref.current?.contains(e.target as Node)) onClose()
    }
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDown)
      document.removeEventListener('keydown', onKey)
    }
  }, [open, onClose])
  return (
    <div ref={ref} className="relative">
      {trigger}
      {open && <div className={cx('animate-popover absolute top-full right-0 z-40 mt-2 w-64 rounded-lg bg-surface-raised p-3 shadow-lg', className)}>{children}</div>}
    </div>
  )
}

/**
 * 가운데(모바일은 아래) 뜨는 대화상자 — 배경을 누르거나 Esc 면 닫힘
 * body 로 portal: 반투명 헤더(backdrop-filter) 안에서 열어도 화면 전체를 덮도록
 */
export function Dialog({ open, onClose, title, children }: {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
}) {
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onClose])
  if (!open) return null
  return createPortal(
    <div className="animate-fade-in fixed inset-0 z-40 flex items-end justify-center bg-overlay sm:items-center sm:p-6" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      {/* 크기 고정: 내용이 바뀌어도 창이 커졌다 작아졌다 하지 않게, 넘치면 안에서 스크롤 */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="flex h-[min(520px,85vh)] w-full flex-col rounded-t-2xl bg-surface shadow-lg sm:w-[420px] sm:rounded-2xl"
      >
        <header className="flex shrink-0 items-center justify-between px-5 pt-4 pb-3">
          <h2 className="text-[17px] font-semibold tracking-tight">{title}</h2>
          <IconButton label="닫기" size="sm" onClick={onClose}>
            <X size={16} />
          </IconButton>
        </header>
        <div className="min-h-0 flex-1 overflow-y-auto px-4 pb-4">{children}</div>
      </div>
    </div>,
    document.body,
  )
}

/** 작은 확인 팝업 — 다른 창 위에 한 겹 더 뜸. Esc·배경 = 취소 (뒤 창은 그대로) */
export function ConfirmDialog({ open, title, detail, confirmLabel, onConfirm, onCancel }: {
  open: boolean
  title: ReactNode
  detail?: ReactNode
  confirmLabel: string
  onConfirm: () => void
  onCancel: () => void
}) {
  useEffect(() => {
    if (!open) return
    // 캡처 단계에서 먼저 받아 뒤의 대화상자까지 Esc 로 닫히지 않게
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return
      e.stopPropagation()
      onCancel()
    }
    document.addEventListener('keydown', onKey, true)
    return () => document.removeEventListener('keydown', onKey, true)
  }, [open, onCancel])
  if (!open) return null
  return createPortal(
    <div className="animate-fade-in fixed inset-0 z-50 flex items-center justify-center bg-overlay p-6" onMouseDown={(e) => e.target === e.currentTarget && onCancel()}>
      <div role="alertdialog" aria-modal="true" className="w-full max-w-[300px] rounded-2xl bg-surface-raised p-5 shadow-lg">
        <p className="text-[16px] font-semibold tracking-tight break-keep">{title}</p>
        {detail && <p className="mt-1 text-[13px] text-fg-muted">{detail}</p>}
        <div className="mt-5 grid grid-cols-2 gap-2">
          <Button onClick={onCancel}>취소</Button>
          <Button variant="primary" autoFocus onClick={onConfirm}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>,
    document.body,
  )
}

/** 이름 입력 + 취소/저장 (Popover 안에서 사용). 같은 이름이 있으면 덮어쓸지 한 번 묻는다 */
export function NameForm({ initial, taken, onSubmit, onCancel }: {
  initial: string
  /** 이미 있는 이름인지 */
  taken?: (name: string) => boolean
  onSubmit: (name: string) => void
  onCancel: () => void
}) {
  const [name, setName] = useState(initial)
  const [confirming, setConfirming] = useState(false)
  const value = name.trim() || initial

  if (confirming) {
    return (
      <div className="space-y-3">
        <p className="text-[14px] leading-snug">
          <span className="font-semibold">{value}</span>
          <br />
          같은 이름이 있어요. 덮어쓸까요?
        </p>
        <div className="flex justify-end gap-1.5">
          <Button variant="ghost" size="sm" onClick={() => setConfirming(false)}>
            취소
          </Button>
          <Button variant="primary" size="sm" autoFocus onClick={() => onSubmit(value)}>
            덮어쓰기
          </Button>
        </div>
      </div>
    )
  }

  return (
    <form
      className="space-y-3"
      onSubmit={(e) => {
        e.preventDefault()
        if (taken?.(value)) setConfirming(true)
        else onSubmit(value)
      }}
    >
      <input
        name="name"
        autoFocus
        value={name}
        onChange={(e) => setName(e.target.value)}
        onFocus={(e) => e.target.select()}
        maxLength={30}
        aria-label="이름"
        className="h-9 w-full rounded-md bg-surface-sunken px-3 text-[15px] outline-none focus:ring-2 focus:ring-accent-soft"
      />
      <div className="flex justify-end gap-1.5">
        <Button variant="ghost" size="sm" onClick={onCancel}>
          취소
        </Button>
        <Button variant="primary" size="sm" type="submit">
          저장
        </Button>
      </div>
    </form>
  )
}

/** '조건 1', '조건 2' … 처럼 이어지는 다음 기본 이름 */
export function nextName(prefix: string, names: string[]) {
  const pattern = new RegExp(`^${prefix} (\\d+)$`)
  const used = names.map((n) => n.match(pattern)?.[1]).filter(Boolean).map(Number)
  return `${prefix} ${Math.max(0, ...used) + 1}`
}

/** iOS UISwitch */
export function Switch({ checked, onChange, label }: { checked: boolean; onChange: (checked: boolean) => void; label: string }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={cx('relative h-[31px] w-[51px] shrink-0 rounded-full transition-colors duration-200', checked ? 'bg-toggle' : 'bg-surface-sunken')}
    >
      <span
        className={cx(
          'absolute top-[2px] left-[2px] size-[27px] rounded-full bg-fg-on-accent shadow-md transition-transform duration-200',
          checked && 'translate-x-5',
        )}
      />
    </button>
  )
}

/** inset grouped 리스트의 한 행: 왼쪽 라벨, 오른쪽 컨트롤 */
export function ListRow({ label, detail, children }: { label: ReactNode; detail?: ReactNode; children?: ReactNode }) {
  return (
    <div className="flex min-h-11 items-center justify-between gap-3 px-4 py-1.5">
      <div className="min-w-0">
        <p className="text-[15px]">{label}</p>
        {detail && <p className="text-[12px] text-fg-muted">{detail}</p>}
      </div>
      {children}
    </div>
  )
}

/** iOS UIStepper: 값 + [− | +] */
export function Stepper({ value, min, max, onChange, label }: {
  value: number
  min: number
  max: number
  onChange: (value: number) => void
  label: string
}) {
  return (
    <div className="flex items-center gap-3" role="group" aria-label={label}>
      <span className="w-7 text-right text-[17px] font-semibold tabular-nums">{value}</span>
      <div className="flex h-8 items-center rounded-sm bg-surface-sunken">
        <button
          type="button"
          aria-label={`${label} 줄이기`}
          disabled={value <= min}
          onClick={() => onChange(value - 1)}
          className="flex h-full w-10 items-center justify-center text-fg transition active:opacity-50 disabled:opacity-25"
        >
          <Minus size={16} strokeWidth={2.4} />
        </button>
        <button
          type="button"
          aria-label={`${label} 늘리기`}
          disabled={value >= max}
          onClick={() => onChange(value + 1)}
          className="flex h-full w-10 items-center justify-center text-fg transition active:opacity-50 disabled:opacity-25"
        >
          <Plus size={16} strokeWidth={2.4} />
        </button>
      </div>
    </div>
  )
}

export function EmptyState({ icon, title, description, action }: {
  icon: ReactNode
  title: string
  description?: ReactNode
  action?: ReactNode
}) {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-16 text-center">
      <div className="mb-4 text-fg-subtle">{icon}</div>
      <p className="text-[17px] font-semibold tracking-tight text-fg">{title}</p>
      {description && <p className="mt-1.5 max-w-80 text-[14px] leading-relaxed text-fg-muted">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}

import { AlertCircle, ChevronRight, Loader2 } from 'lucide-react'
import { cx } from '../components/ui'
import type { GenerationState } from '../lib/data'

/**
 * 실시간 결과 요약 — 설정을 바꾸는 바로 그 화면에서 재계산 결과를 보여줌
 * sidebar: 데스크톱 왼쪽 패널 하단 / floating: 모바일 탭 바 위 (누르면 시간표 탭으로)
 */
export function ResultSummary({ generation, credits, variant, onOpen }: {
  generation: GenerationState
  credits: number | null
  variant: 'sidebar' | 'floating'
  onOpen?: () => void
}) {
  const content = (() => {
    switch (generation.status) {
      case 'idle':
        return <span className="text-fg-muted">강의를 담으면 시간표가 바로 만들어져요</span>
      case 'error':
        return (
          <span className="flex items-center gap-1.5 text-danger">
            <AlertCircle size={15} /> 조건에 맞는 조합을 만들 수 없어요
          </span>
        )
      case 'running':
        return (
          <span className="flex items-center gap-1.5 text-fg-muted">
            <Loader2 size={15} className="animate-spin" /> 다시 계산 중…
          </span>
        )
      case 'done': {
        const count = generation.output.schedules.length
        return (
          <span className="min-w-0">
            <span className="text-fg-muted">가능한 조합 </span>
            <span key={count} className={cx('animate-pop font-semibold tabular-nums', count === 0 ? 'text-danger' : 'text-fg')}>
              {count.toLocaleString()}
            </span>
            <span className="text-fg-muted">개</span>
            {credits !== null && count > 0 && (
              <>
                <span className="text-fg-subtle"> · </span>
                <span key={`c${credits}`} className="animate-pop font-semibold text-fg tabular-nums">
                  {credits}
                </span>
                <span className="text-fg-muted">학점</span>
              </>
            )}
          </span>
        )
      }
    }
  })()

  if (variant === 'sidebar') {
    return (
      <div aria-live="polite" className="mx-4 mb-4 flex min-h-11 items-center rounded-lg bg-surface-raised px-4 text-[14px] shadow-sm">
        {content}
      </div>
    )
  }
  return (
    <button
      type="button"
      onClick={onOpen}
      aria-live="polite"
      className="material fixed inset-x-4 bottom-[92px] z-30 flex h-12 items-center justify-between gap-2 rounded-full pr-3 pl-5 text-left text-[14px] shadow-lg active:scale-[0.99]"
    >
      {content}
      <span className="flex shrink-0 items-center text-[13px] font-semibold text-accent-fg">
        시간표 보기 <ChevronRight size={16} strokeWidth={2.5} />
      </span>
    </button>
  )
}

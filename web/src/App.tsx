import { BookOpen, Bookmark, CalendarRange, Loader2, Monitor, Moon, Search, SlidersHorizontal, Sun } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { cx, IconButton, Segmented, Toast, type ToastData } from './components/ui'
import { BasketPanel } from './features/BasketPanel'
import { ConditionsButton } from './features/ConditionsDialog'
import { ConstraintsPanel } from './features/ConstraintsPanel'
import { ResultSummary } from './features/ResultSummary'
import { ResultView } from './features/ResultView'
import type { PreviewItem } from './features/Timetable'
import { SavedPanel } from './features/SavedPanel'
import { SearchPanel } from './features/SearchPanel'
import { useCourses, useGeneration, useTerms } from './lib/data'
import { useConfig, useSaved, useStore, type ThemePref } from './lib/store'
import { describeChange, EMPTY_VIEWER, reconcileViewer, scheduleKey, type ViewerState } from './lib/viewer'
import type { GenerationOutput, ScheduleConfig } from './engine/types'

type Tab = 'search' | 'basket' | 'constraints' | 'saved' | 'result'

export default function App() {
  const { state, dispatch } = useStore()
  const config = useConfig()
  const { terms, error: termsError } = useTerms()
  const { courses, error: coursesError } = useCourses(state.termKey)
  const generation = useGeneration(state.termKey, courses, config)
  const [tab, setTab] = useState<Tab>('search')
  const isDesktop = useMediaQuery('(min-width: 1024px)')

  useResolvedTheme(state.theme)

  // ── 보기 상태 (보던 시간표·고정) + 재계산 알림 ──
  const [viewer, setViewer] = useState<ViewerState>(EMPTY_VIEWER)
  const viewerRef = useRef(viewer)
  viewerRef.current = viewer
  const [toast, setToast] = useState<ToastData | null>(null)
  const notify = useCallback((message: string, action?: ToastData['action']) => setToast({ id: Date.now() + Math.random(), message, action }), [])
  // 항상 최신 학기만 사용. 새 학기 데이터가 올라오면 그 학기로 넘어가고 한 번 알림
  const term = terms?.[0] ?? null
  useEffect(() => {
    if (!term || state.termKey === term.key) return
    if (state.termKey) notify(`${term.label} 강의로 바뀌었어요`)
    dispatch({ type: 'setTerm', termKey: term.key })
  }, [term, state.termKey, dispatch, notify])

  useEffect(() => {
    if (!toast) return
    const t = setTimeout(() => setToast(null), toast.action ? 5000 : 3200)
    return () => clearTimeout(t)
  }, [toast])

  /** 마지막으로 반영한 결과 (변화량 계산·되돌리기용) */
  const lastRef = useRef<{ termKey: string; config: ScheduleConfig; count: number; output: GenerationOutput | null } | null>(null)
  const undoingRef = useRef(false)
  /** 되돌리기 할 때 복원할, 설정을 바꾸기 직전의 보기 상태 */
  const undoViewerRef = useRef<ViewerState | null>(null)

  useEffect(() => {
    if (generation.status === 'idle') {
      lastRef.current = null
      return
    }
    if (generation.status === 'running' || !courses) return
    const prev = lastRef.current
    const output = generation.status === 'done' ? generation.output : null
    if (prev && prev.config === generation.config && prev.termKey === generation.termKey && prev.output === output) return
    const count = output ? output.schedules.length : 0

    // 보던 시간표·고정을 새 결과에 맞춤 (학기가 바뀌면 처음부터)
    const sameTerm = prev?.termKey === generation.termKey
    const viewerBefore = viewerRef.current
    const base = !sameTerm ? EMPTY_VIEWER : undoingRef.current && undoViewerRef.current ? undoViewerRef.current : viewerBefore
    const reconciled = output ? reconcileViewer(base, output.schedules, new Map(courses.map((c) => [c.id, c]))) : null
    if (reconciled) setViewer(reconciled.viewer)

    // 같은 학기에서 설정이 바뀌어 눈에 보이는 변화가 있을 때만 짧게 알림 + 되돌리기
    if (prev && sameTerm && prev.config !== generation.config) {
      const undo = undoingRef.current
      undoingRef.current = false
      const lostView = !undo && !!reconciled?.lostView
      const dropped = reconciled?.droppedPins.length ?? 0
      const what = describeChange(prev.config, generation.config)
      const isListChange = /담음|뺌|옮김/.test(what)
      if (undo || count !== prev.count || lostView || dropped) {
        const message = undo
          ? '되돌렸어요'
          : [
              count === 0
                ? `${what} → 조합 없음`
                : // 담기·빼기·옮기기는 무엇이 바뀌었는지 앞에 붙임
                  `${isListChange ? `${what} · ` : ''}조합 ${prev.count.toLocaleString()} → ${count.toLocaleString()}개`,
              lostView && count > 0 && '보던 시간표 바뀜',
              dropped > 0 && `고정 ${dropped}개 풀림`,
            ]
              .filter(Boolean)
              .join(' · ')
        const prevConfig = prev.config
        notify(
          message,
          undo
            ? undefined
            : {
                label: '되돌리기',
                onClick: () => {
                  undoingRef.current = true
                  undoViewerRef.current = viewerBefore
                  dispatch({ type: 'replaceConfig', config: prevConfig })
                },
              },
        )
      }
    }
    lastRef.current = { termKey: generation.termKey, config: generation.config, count, output }
  }, [generation, courses, dispatch, notify])

  const shownOutput = generation.status === 'done' ? generation.output : generation.status === 'running' ? generation.previous : null
  const currentSchedule = useMemo(() => {
    if (!shownOutput) return null
    return (viewer.key ? shownOutput.schedules.find((x) => scheduleKey(x) === viewer.key) : shownOutput.schedules[0]) ?? null
  }, [shownOutput, viewer.key])
  const currentCredits = currentSchedule?.totalCredits ?? null

  /** 강의 검색에서 펼친 과목·분반을 시간표에 흐릿하게 미리보기 */
  const [preview, setPreview] = useState<PreviewItem[] | null>(null)
  useEffect(() => {
    if (tab !== 'search') setPreview(null)
  }, [tab])

  const basketCount = config.required.length + config.desired.length

  /** 저장 탭에서 연 시간표 (모바일은 열면 시간표 화면으로) */
  const savedCount = useSaved().length
  const [savedView, setSavedView] = useState<string | null>(null)
  const openSaved = (id: string | null) => {
    setSavedView(id)
    if (id && !isDesktop) setTab('result')
  }
  const resultCount = generation.status === 'done' ? generation.output.schedules.length : null
  const error = termsError || coursesError

  const sidebarTabs: { value: Exclude<Tab, 'result'>; label: ReactNode }[] = [
    { value: 'search', label: '강의 검색' },
    { value: 'basket', label: <>담은 강의{basketCount > 0 && <Count n={basketCount} />}</> },
    { value: 'constraints', label: '조건' },
    { value: 'saved', label: <>저장{savedCount > 0 && <Count n={savedCount} />}</> },
  ]
  const sidebarTab = tab === 'result' ? 'search' : tab

  const panel = (t: Exclude<Tab, 'result'>) =>
    !courses ? (
      <Loading />
    ) : t === 'search' ? (
      <SearchPanel courses={courses} onPreview={setPreview} />
    ) : t === 'basket' ? (
      <div className="h-full overflow-y-auto">
        <BasketPanel courses={courses} onBrowse={() => setTab('search')} />
      </div>
    ) : t === 'saved' ? (
      <div className="h-full overflow-y-auto">
        <SavedPanel courses={courses} activeId={savedView} onOpen={openSaved} notify={notify} />
      </div>
    ) : (
      <div className="h-full overflow-y-auto">
        <ConstraintsPanel />
      </div>
    )

  const results = courses && (
    <ResultView
      generation={generation}
      courses={courses}
      onAddCourses={() => setTab('search')}
      emptyGrid={isDesktop}
      viewer={viewer}
      onViewerChange={setViewer}
      notify={notify}
      preview={isDesktop ? preview : null}
      savedView={savedView}
      onSavedViewChange={setSavedView}
    />
  )

  const controls = (
    <>
      <ConditionsButton notify={notify} onApplied={() => setSavedView(null)} />
      <ThemeButton />
    </>
  )
  const errorBanner = error && <p className="mx-4 mt-2 rounded-md bg-danger-soft px-4 py-2.5 text-[13px] text-danger lg:mx-10">{error}</p>

  if (isDesktop) {
    /* 데스크톱 (macOS 앱 구조): 회색 사이드바 + 흰 메인, 구분선 없이 배경 대비로만 나눔 */
    return (
      <div className="flex h-full">
        <aside className="flex shrink-0 flex-col bg-surface" style={{ width: 'var(--layout-sidebar-width)' }}>
          <div className="flex items-center gap-3 px-6 pt-5 pb-4">
            <Logo />
            <div className="min-w-0">
              <h1 className="truncate text-[17px] leading-tight font-semibold tracking-tight">시간표 생성기</h1>
              <p className="text-[12px] leading-tight text-fg-muted">명지대학교{term && ` · ${term.label}`}</p>
            </div>
          </div>
          <div className="px-4 pb-3">
            <Segmented value={sidebarTab} onChange={setTab} options={sidebarTabs} />
          </div>
          {/* 데스크톱은 결과가 바로 옆에 보이므로 요약 바 없이 (정보 중복) */}
          <div className="min-h-0 flex-1">{panel(sidebarTab)}</div>
        </aside>
        <div className="flex min-w-0 flex-1 flex-col">
          <header className="material sticky top-0 z-30 flex shrink-0 items-center justify-end gap-1.5 px-8" style={{ height: 'var(--layout-header-height)' }}>
            {controls}
          </header>
          {errorBanner}
          <main className="min-w-0 flex-1 overflow-y-auto px-10 pt-2 pb-12">{results}</main>
        </div>
        <Toast toast={toast} onClose={() => setToast(null)} className="bottom-8" />
      </div>
    )
  }

  /* 모바일 (iOS 앱 구조): 반투명 내비게이션 바 + 떠 있는 캡슐 탭 바 */
  return (
    <div className={cx('flex h-full flex-col', tab === 'result' ? 'bg-bg' : 'bg-surface')}>
      <header className="material sticky top-0 z-30 flex shrink-0 items-center gap-2.5 px-4" style={{ height: 'var(--layout-header-height)' }}>
        <Logo />
        <h1 className="hidden text-[17px] font-semibold tracking-tight min-[420px]:block">시간표 생성기</h1>
        {term && <span className="text-[12px] text-fg-muted">{term.label}</span>}
        <div className="ml-auto flex items-center gap-1">{controls}</div>
      </header>
      {errorBanner}
      <div className={cx('min-h-0 flex-1 overflow-y-auto pt-2', tab === 'result' ? 'pb-28' : 'pb-44')}>
        {tab === 'result' ? <div className="px-4">{results}</div> : panel(tab)}
      </div>
      {tab !== 'result' && <ResultSummary generation={generation} credits={currentCredits} variant="floating" onOpen={() => setTab('result')} />}
      <Toast toast={toast} onClose={() => setToast(null)} className={tab === 'result' ? 'bottom-24' : 'bottom-[152px]'} />
      <nav className="material fixed inset-x-4 bottom-4 z-30 grid h-16 grid-cols-5 rounded-full p-1 shadow-lg">
        <NavItem active={tab === 'search'} onClick={() => setTab('search')} icon={<Search size={20} />} label="검색" />
        <NavItem active={tab === 'basket'} onClick={() => setTab('basket')} icon={<BookOpen size={20} />} label="담은 강의" badge={basketCount || undefined} />
        <NavItem active={tab === 'constraints'} onClick={() => setTab('constraints')} icon={<SlidersHorizontal size={20} />} label="조건" />
        <NavItem active={tab === 'saved'} onClick={() => setTab('saved')} icon={<Bookmark size={20} />} label="저장" badge={savedCount || undefined} />
        <NavItem
          active={tab === 'result'}
          onClick={() => setTab('result')}
          icon={generation.status === 'running' ? <Loader2 size={20} className="animate-spin" /> : <CalendarRange size={20} />}
          label="시간표"
          badge={resultCount ?? undefined}
        />
      </nav>
    </div>
  )
}

function Logo() {
  return (
    <div className="flex size-9 shrink-0 items-center justify-center rounded-[10px] bg-accent shadow-sm">
      <svg viewBox="0 0 32 32" className="size-[22px]" aria-hidden>
        <rect x="5" y="6" width="9" height="8" rx="2.5" fill="white" />
        <rect x="18" y="6" width="9" height="14" rx="2.5" fill="white" opacity=".75" />
        <rect x="5" y="18" width="9" height="8" rx="2.5" fill="white" opacity=".75" />
      </svg>
    </div>
  )
}

function Count({ n }: { n: number }) {
  return <span className="text-[12px] font-semibold text-accent-fg tabular-nums">{n}</span>
}

function NavItem({ active, onClick, icon, label, badge }: { active: boolean; onClick: () => void; icon: ReactNode; label: string; badge?: number }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-current={active}
      className={cx(
        'relative flex flex-col items-center justify-center gap-0.5 rounded-full text-[10px] font-medium transition-colors',
        active ? 'bg-surface-sunken text-accent-fg' : 'text-fg-muted',
      )}
    >
      {icon}
      {label}
      {badge !== undefined && (
        <span className="absolute top-1.5 left-1/2 ml-2.5 rounded-full bg-accent px-1.5 text-[10px] leading-4 font-semibold text-fg-on-accent tabular-nums">
          {badge > 999 ? '999+' : badge}
        </span>
      )}
    </button>
  )
}

function Loading() {
  return (
    <div className="flex items-center justify-center gap-2 py-16 text-sm text-fg-muted">
      <Loader2 size={16} className="animate-spin" /> 강의 데이터를 불러오는 중…
    </div>
  )
}

function ThemeButton() {
  const { state, dispatch } = useStore()
  const order: ThemePref[] = ['system', 'light', 'dark']
  const icon = { system: <Monitor size={16} />, light: <Sun size={16} />, dark: <Moon size={16} /> }[state.theme]
  const label = { system: '시스템 테마', light: '라이트 테마', dark: '다크 테마' }[state.theme]
  return (
    <IconButton label={`${label} (눌러서 변경)`} onClick={() => dispatch({ type: 'setTheme', theme: order[(order.indexOf(state.theme) + 1) % 3] })}>
      {icon}
    </IconButton>
  )
}

function useMediaQuery(query: string) {
  const [matches, setMatches] = useState(() => window.matchMedia(query).matches)
  useEffect(() => {
    const media = window.matchMedia(query)
    const onChange = () => setMatches(media.matches)
    media.addEventListener('change', onChange)
    return () => media.removeEventListener('change', onChange)
  }, [query])
  return matches
}

/** system 이면 OS 설정을 따라 data-theme 을 light/dark 로 맞춤 */
function useResolvedTheme(pref: ThemePref) {
  useEffect(() => {
    const media = window.matchMedia('(prefers-color-scheme: dark)')
    const apply = () => {
      const theme = pref === 'system' ? (media.matches ? 'dark' : 'light') : pref
      document.documentElement.dataset.theme = theme
    }
    apply()
    media.addEventListener('change', apply)
    return () => media.removeEventListener('change', apply)
  }, [pref])
}

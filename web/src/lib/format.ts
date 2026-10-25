import { MAX_RESULTS } from '../engine/types'

/** 상한(10,000개)에 닿은 조합 수인지 — 실제로는 더 있을 수 있음 */
export const isCapped = (count: number) => count >= MAX_RESULTS

/** '10,000+' (숫자만: 페이지 넘김 등) */
export const formatCount = (count: number) => `${count.toLocaleString()}${isCapped(count) ? '+' : ''}`

/** '6,000개' / '10,000개+' */
export const countLabel = (count: number) => `${count.toLocaleString()}개${isCapped(count) ? '+' : ''}`

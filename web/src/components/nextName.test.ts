import { describe, expect, it } from 'vitest'
import { nextName } from './ui'

describe('nextName', () => {
  it('이어지는 번호를 붙인다', () => {
    expect(nextName('조건', [])).toBe('조건 1')
    expect(nextName('조건', ['조건 1', '조건 3', '내 조건'])).toBe('조건 4')
    expect(nextName('시간표', ['조건 7'])).toBe('시간표 1')
  })
})

import React, { useState } from 'react'
import './UserInputForm.css'

function UserInputForm({ onSubmit, loading, selectedMemeKeyword, selectedCardKeyword }) {
  const [form, setForm] = useState({
    age: '20-30대',
    job: '직장인',
    category: '패션',
    budget: '중간',
    focus: '신규 고객',
    free_input: ''
  })

  const handleChange = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit(form)
  }

  return (
    <form className="user-form" onSubmit={handleSubmit}>

      {/* 선택된 키워드 요약 */}
      <div className="selected-keywords-summary">
        <h4>선택된 키워드 (Step 1-2에서 클릭)</h4>
        <div className="selected-keyword-row">
          <span className="selected-label meme-label">소셜 트렌드</span>
          {selectedMemeKeyword
            ? <span className="selected-value">{selectedMemeKeyword.keyword} — {selectedMemeKeyword.explanation || '설명 없음'}</span>
            : <span className="selected-empty">왼쪽 패널에서 소셜 급등 키워드를 클릭하세요</span>
          }
        </div>
        <div className="selected-keyword-row">
          <span className="selected-label card-label">카드 이벤트</span>
          {selectedCardKeyword
            ? <span className="selected-value">{selectedCardKeyword.category} — {selectedCardKeyword.explanation || '설명 없음'}</span>
            : <span className="selected-empty">왼쪽 패널에서 카드 카테고리를 클릭하세요</span>
          }
        </div>
      </div>
      <label>연령대
        <select value={form.age} onChange={(e) => handleChange('age', e.target.value)}>
          <option>10-20대</option>
          <option>20-30대</option>
          <option>30-40대</option>
          <option>40-50대</option>
          <option>50대+</option>
          <option>전체</option>
        </select>
      </label>

      <label>직업/직군
        <select value={form.job} onChange={(e) => handleChange('job', e.target.value)}>
          <option>학생</option>
          <option>직장인</option>
          <option>자영업자</option>
          <option>전문직</option>
          <option>주부</option>
          <option>전체</option>
        </select>
      </label>

      <label>관심 카테고리
        <select value={form.category} onChange={(e) => handleChange('category', e.target.value)}>
          <option>패션</option>
          <option>뷰티</option>
          <option>음식</option>
          <option>여행</option>
          <option>전자제품</option>
          <option>생활용품</option>
          <option>전체</option>
        </select>
      </label>

      <label>예산 할당
        <select value={form.budget} onChange={(e) => handleChange('budget', e.target.value)}>
          <option>저예산</option>
          <option>중간</option>
          <option>고예산</option>
          <option>프리미엄</option>
        </select>
      </label>

      <label>마케팅 포커스
        <select value={form.focus} onChange={(e) => handleChange('focus', e.target.value)}>
          <option>신규 고객</option>
          <option>기존 고객</option>
          <option>구매 촉진</option>
          <option>브랜드 인지</option>
          <option>전체</option>
        </select>
      </label>

      <label>추가 요청사항 (자유 입력)
        <textarea
          value={form.free_input}
          onChange={(e) => handleChange('free_input', e.target.value)}
          placeholder="예: 여름 분위기, 밝은 톤, 20대 여성 타겟..."
          rows={3}
        />
      </label>

      <button type="submit" disabled={loading}>
        {loading ? '생성 중...' : 'Step 4: 이미지 프롬프트 생성'}
      </button>
    </form>
  )
}

export default UserInputForm

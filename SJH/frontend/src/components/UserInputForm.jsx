import React, { useState } from 'react'
import './UserInputForm.css'

function UserInputForm({ onSubmit, loading }) {
  const [form, setForm] = useState({
    age: '20-30대',
    job: '직장인',
    category: '패션',
    budget: '중간',
    focus: '신규 고객'
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

      <button type="submit" disabled={loading}>
        {loading ? '생성 중...' : 'Step 4: 홍보물 생성'}
      </button>
    </form>
  )
}

export default UserInputForm

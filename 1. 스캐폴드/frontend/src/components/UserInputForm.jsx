import { useState } from 'react'
import './UserInputForm.css'

function UserInputForm({ onSubmit, loading }) {
  const [formData, setFormData] = useState({
    ageGroup: '20-30대',
    job: '직장인',
    category: '패션',
    budget: '중간',
    focus: '신규 고객'
  })

  const ageGroups = ['10-20대', '20-30대', '30-40대', '40-50대', '50대+', '전체']
  const jobs = ['학생', '직장인', '자영업자', '전문직', '주부', '전체']
  const categories = ['패션', '뷰티', '음식', '여행', '전자제품', '생활용품', '전체']
  const budgets = ['저예산', '중간', '고예산', '프리미엄']
  const focuses = ['신규 고객', '기존 고객', '구매 촉진', '브랜드 인지', '전체']

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <form className="user-input-form" onSubmit={handleSubmit}>
      <h3>🎯 Step 3: 타겟 오디언스 설정</h3>
      <p className="form-subtitle">마케팅 캠페인에 맞는 정보를 입력해주세요</p>

      <div className="form-group">
        <label htmlFor="ageGroup">연령대</label>
        <select 
          id="ageGroup"
          name="ageGroup"
          value={formData.ageGroup}
          onChange={handleChange}
        >
          {ageGroups.map(group => (
            <option key={group} value={group}>{group}</option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="job">직업/직군</label>
        <select 
          id="job"
          name="job"
          value={formData.job}
          onChange={handleChange}
        >
          {jobs.map(job => (
            <option key={job} value={job}>{job}</option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="category">관심 카테고리</label>
        <select 
          id="category"
          name="category"
          value={formData.category}
          onChange={handleChange}
        >
          {categories.map(cat => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="budget">예산 할당</label>
        <select 
          id="budget"
          name="budget"
          value={formData.budget}
          onChange={handleChange}
        >
          {budgets.map(b => (
            <option key={b} value={b}>{b}</option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="focus">마케팅 포커스</label>
        <select 
          id="focus"
          name="focus"
          value={formData.focus}
          onChange={handleChange}
        >
          {focuses.map(f => (
            <option key={f} value={f}>{f}</option>
          ))}
        </select>
      </div>

      <button 
        type="submit" 
        className="submit-btn"
        disabled={loading}
      >
        {loading ? '🔄 생성 중...' : '✨ Step 4: 홍보물 생성'}
      </button>
    </form>
  )
}

export default UserInputForm

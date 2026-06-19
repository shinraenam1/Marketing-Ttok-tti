import React from 'react'
import './PromotionalContent.css'

function PromotionalContent({ content, params, onReset }) {
  return (
    <div className="promo-wrap">
      <h3>생성된 홍보 콘텐츠</h3>
      {params && (
        <p className="promo-meta">
          타겟: {params.age} / {params.job} / {params.category}
        </p>
      )}
      <pre className="promo-content">{content}</pre>
      <button type="button" onClick={onReset}>다시 생성하기</button>
    </div>
  )
}

export default PromotionalContent

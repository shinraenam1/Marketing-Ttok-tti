import './PromotionalContent.css'

function PromotionalContent({ content, params, onReset }) {
  // Parse promotional content sections
  const sections = content.split('###').filter(s => s.trim())
  
  return (
    <div className="promotional-content">
      <div className="content-header">
        <h3>📢 Step 4: 생성된 홍보물</h3>
        <div className="params-badge">
          {params && (
            <>
              <span>👥 {params.ageGroup}</span>
              <span>💼 {params.job}</span>
              <span>🏷️ {params.category}</span>
            </>
          )}
        </div>
      </div>

      <div className="promotional-sections">
        {sections.map((section, idx) => {
          const [title, ...contentParts] = section.trim().split('\n')
          const sectionContent = contentParts.join('\n').trim()
          
          const sectionNum = idx + 1
          let icon = '📄'
          if (title.includes('배너')) icon = '🎨'
          else if (title.includes('SNS')) icon = '📱'
          else if (title.includes('이메일')) icon = '📧'

          return (
            <div key={idx} className="promo-section">
              <h4>{icon} {sectionNum}. {title.trim()}</h4>
              <div className="section-content">
                {sectionContent.split('\n').map((line, lineIdx) => {
                  if (line.trim().startsWith('-')) {
                    return <li key={lineIdx}>{line.trim().substring(1).trim()}</li>
                  } else if (line.trim()) {
                    return <p key={lineIdx}>{line}</p>
                  }
                  return null
                })}
              </div>
            </div>
          )
        })}
      </div>

      <div className="action-buttons">
        <button 
          className="copy-btn"
          onClick={() => {
            navigator.clipboard.writeText(content)
            alert('클립보드에 복사되었습니다!')
          }}
        >
          📋 모두 복사
        </button>
        <button 
          className="reset-btn"
          onClick={onReset}
        >
          🔄 다시 생성
        </button>
      </div>
    </div>
  )
}

export default PromotionalContent

import React from 'react'
import './PromotionalContent.css'

function PromotionalContent({ content, params, imageDataUrl, videoDataUrl, assetErrors = [], onReset }) {
  return (
    <div className="promo-wrap">
      <h3>생성된 홍보 콘텐츠</h3>
      {params && (
        <p className="promo-meta">
          타겟: {params.age} / {params.job} / {params.category}
        </p>
      )}
      <pre className="promo-content">{content}</pre>

      <div className="media-grid">
        <div className="media-card">
          <h4>생성 이미지</h4>
          {imageDataUrl ? (
            <img
              className="promo-image"
              src={imageDataUrl}
              alt="생성된 광고 이미지"
            />
          ) : (
            <p className="media-empty">이미지 생성 결과가 없습니다.</p>
          )}
        </div>

        <div className="media-card">
          <h4>생성 동영상</h4>
          {videoDataUrl ? (
            <video
              className="promo-video"
              src={videoDataUrl}
              controls
              playsInline
            />
          ) : (
            <p className="media-empty">동영상 생성 결과가 없습니다.</p>
          )}
        </div>
      </div>

      {Array.isArray(assetErrors) && assetErrors.length > 0 && (
        <div className="asset-errors">
          {assetErrors.map((err, idx) => (
            <p key={idx}>{err}</p>
          ))}
        </div>
      )}

      <button type="button" onClick={onReset}>다시 생성하기</button>
    </div>
  )
}

export default PromotionalContent

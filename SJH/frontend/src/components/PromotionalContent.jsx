import React, { useEffect, useState } from 'react'
import './PromotionalContent.css'

function PromotionalContent({ content, params, imageDataUrl, videoDataUrl, assetErrors = [], onReset }) {
  const [zoomOpen, setZoomOpen] = useState(false)
  const [galleryOpen, setGalleryOpen] = useState(false)
  const isComplete = !!(imageDataUrl && videoDataUrl)

  useEffect(() => {
    if (!zoomOpen) {
      return undefined
    }

    const onKeyDown = (event) => {
      if (event.key === 'Escape') {
        setZoomOpen(false)
      }
    }

    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [zoomOpen])

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
            <>
              <button
                type="button"
                className="image-zoom-trigger"
                onClick={() => setZoomOpen(true)}
                aria-label="생성된 이미지 확대 보기"
              >
                <img
                  className="promo-image"
                  src={imageDataUrl}
                  alt="생성된 광고 이미지"
                />
              </button>
              <p className="media-hint">이미지를 클릭하면 확대됩니다.</p>
            </>
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

      <div className="button-group">
        <button type="button" onClick={onReset}>다시 생성하기</button>
        {isComplete && (
          <button
            type="button"
            className="view-gallery-btn"
            onClick={() => setGalleryOpen(true)}
          >
            홍보물 확인
          </button>
        )}
      </div>

      {zoomOpen && imageDataUrl && (
        <div
          className="image-zoom-backdrop"
          onClick={() => setZoomOpen(false)}
          role="presentation"
        >
          <div
            className="image-zoom-dialog"
            onClick={(event) => event.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="생성된 이미지 확대"
          >
            <button
              type="button"
              className="zoom-close"
              onClick={() => setZoomOpen(false)}
              aria-label="확대 보기 닫기"
            >
              닫기
            </button>
            <img
              className="zoomed-image"
              src={imageDataUrl}
              alt="확대된 생성 이미지"
            />
          </div>
        </div>
      )}

      {galleryOpen && isComplete && (
        <div
          className="gallery-backdrop"
          onClick={() => setGalleryOpen(false)}
          role="presentation"
        >
          <div
            className="gallery-modal"
            onClick={(event) => event.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-label="생성 콘텐츠 갤러리"
          >
            <button
              type="button"
              className="gallery-close"
              onClick={() => setGalleryOpen(false)}
              aria-label="갤러리 닫기"
            >
              ✕
            </button>

            <div className="gallery-content">
              <div className="gallery-section image-section">
                <h3>광고 이미지</h3>
                <img
                  className="gallery-image"
                  src={imageDataUrl}
                  alt="생성된 광고 이미지"
                />
              </div>

              <div className="gallery-section video-section">
                <h3>광고 영상</h3>
                <video
                  className="gallery-video"
                  src={videoDataUrl}
                  controls
                  playsInline
                  controlsList="nodownload"
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default PromotionalContent

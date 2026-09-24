# Vertical Split Design Tokens

## Colour roles

- Canvas: `#f6f5f4`
- Card surface: `#ffffff`
- Primary ink: `#000000`
- Body copy: `#615d59`
- Muted copy: `#757575`
- Hairline border: `rgba(0, 0, 0, 0.08)`
- Primary action: `#b84a32`
- Primary hover: `#9f3d29`
- Brand terracotta: `#cf6041`
- Secondary action surface: `#f7e5dd`
- Warm orange highlight: `#d97845`
- Peach highlight: `#f3d7c8`
- Dark preview island: `#02093a`
- Error: `#b42318`

Dark mode maps the same semantic roles to warm charcoal surfaces (`#191918` canvas, `#242423` cards, `#1e1e1d` fields) with off-white ink (`#f7f6f3`). Terracotta remains the single interactive accent.

## Typography

- UI: Inter when installed, then the device system sans-serif.
- Editorial intro: Source Serif Pro when installed, then Georgia.
- Display: `clamp(40px, 11vw, 54px)`, weight 650, line-height 1.04, tracking -0.036em.
- Section heading: 20px, weight 600-700, line-height 1.2.
- Body: 16px, line-height 1.5.
- UI label: 14px, weight 500.
- Caption/status: 11-12px, weight 600-700.

## Shape, spacing and motion

- Base spacing unit: 4px.
- Common gaps: 8px, 12px, 16px, 20px, 24px.
- Cards: 12px radius.
- Buttons and fields: 8px radius.
- Pills: 9999px radius.
- Minimum interactive height: 48px.
- Standard transition: 200ms ease.
- Reduced-motion preference removes meaningful transition duration.

## Elevation

Content cards use hairline borders and no shadow. Only the video preview uses a small `0 4px 12px` shadow because it is treated as an embedded media mock-up.

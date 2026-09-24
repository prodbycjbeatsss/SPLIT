# Vertical Split Design System

## Direction

SPLIT uses a warm paper notebook aesthetic adapted to a compact Android utility. Light mode uses a warm canvas, white cards, near-black text and one terracotta primary action. Dark mode preserves the same hierarchy with warm charcoal surfaces rather than relying on browser recolouring. Orange accents connect the interface to the cut-paper logo without competing with the task.

## Components

### App header

The sticky 64px header uses the compact play-panel mark with the `SPL/T.v8` wordmark on the left. GitHub and the saved theme toggle sit on the right. There is no marketing hero or tagline, keeping the export controls above the fold.

### File picker

The picker uses the pale terracotta secondary-action surface, a dashed terracotta border and a full-area label target. Hover and keyboard focus increase border clarity without a shadow.

### Form fields

Every main field is at least 48px tall, uses an 8px radius and gains a terracotta border plus focus ring. Clip-name fields are a compact 38px within an already labelled list row. Labels remain visible above main fields. The crop percentage supplements the slider position numerically.

### Primary action

Each view has one filled terracotta action: Batch export. Disabled state uses opacity in addition to its native disabled behaviour. Download is the primary action only after processing completes.

### Secondary action

Process another and View use the pale terracotta ghost treatment. They never compete with the current primary action. Browser-engine loading, encoding and packaging remain progress states rather than separate screens.

### Clip overview

Rows use white surfaces and hairline borders. Before export, each row contains an editable filename with a visible timestamp. Status is communicated with text inside pills, so it never relies on colour alone. After export, the same list becomes an in-app player index with one expanded video at a time.

### Progress and result panels

Both use the sky-tint surface to distinguish transient workflow information. Error copy uses a dark red with semibold text.

### Video preview

The preview is the one dark-mode island. Midnight framing focuses attention on the media and keeps the video controls legible. The preview alone may use a small shadow.

## Responsive behaviour

- Below 620px: one-column controls and actions.
- At 620px and above: two-column controls and result actions; crop control spans both columns.
- The main content remains capped at 800px for comfortable scanning.

## Accessibility

- Interactive controls are at least 48px high.
- Keyboard focus uses a visible terracotta ring.
- Status text accompanies every status colour.
- `prefers-reduced-motion` is respected.
- UI fonts use local system fallbacks so the app remains fully offline.
- The app owns its light/dark theme and opts out of extension-driven recolouring.
- Processing status explicitly tells mobile users to keep the page open and the screen awake.

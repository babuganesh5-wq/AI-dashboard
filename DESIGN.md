---
version: alpha
name: Antigravity-AI-design-spec
description: "A premium, high-density dark glassmorphism system engineered for agentic SaaS workflows. The system features a void-black canvas (#030712) with a five-step surface hierarchy using frosted semi-transparent backdrops, accented by neon cyan (#06b6d4), indigo-blue (#6366f1), and fuchsia-pink (#d946ef). Interactive components react with micro-animations, neon-tinted border elevations, and soft ambient drop shadows. Font weights favor clean Space Grotesk headings paired with high-contrast Plus Jakarta Sans body and JetBrains Mono telemetries."

colors:
  primary-cyan: "#06b6d4"
  primary-indigo: "#6366f1"
  primary-fuchsia: "#d946ef"
  semantic-success: "#10b981"
  semantic-warning: "#f59e0b"
  semantic-danger: "#ef4444"
  crm-orange: "#f97316"
  canvas: "#030712"
  surface-card: "rgba(255, 255, 255, 0.03)"
  surface-panel: "rgba(0, 0, 0, 0.35)"
  hairline: "rgba(255, 255, 255, 0.05)"
  hairline-active: "rgba(6, 182, 212, 0.2)"
  ink: "#f8fafc"
  ink-muted: "#cbd5e1"
  ink-subtle: "#64748b"

typography:
  display-xl:
    fontFamily: Space Grotesk
    fontSize: 56px
    fontWeight: 700
    lineHeight: 1.10
    letterSpacing: -1.5px
  display-lg:
    fontFamily: Space Grotesk
    fontSize: 40px
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: -1.0px
  headline:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: -0.5px
  card-title:
    fontFamily: Space Grotesk
    fontSize: 16px
    fontWeight: 600
    lineHeight: 1.30
    letterSpacing: -0.2px
  body:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.50
    letterSpacing: 0
  body-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.50
    letterSpacing: 0
  caption:
    fontFamily: Plus Jakarta Sans
    fontSize: 10px
    fontWeight: 400
    lineHeight: 1.40
    letterSpacing: 0.2px
  eyebrow:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: 600
    lineHeight: 1.30
    letterSpacing: 1.5px
  mono:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.50
    letterSpacing: 0

rounded:
  xs: 4px
  sm: 6px
  md: 8px
  lg: 12px
  xl: 16px
  pill: 9999px
  full: 9999px

spacing:
  xxs: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  xxl: 48px

components:
  glass-card:
    backgroundColor: "{colors.surface-card}"
    borderColor: "{colors.hairline}"
    backdropFilter: "blur(12px)"
    rounded: "{rounded.lg}"
    padding: 16px
  glass-panel:
    backgroundColor: "{colors.surface-panel}"
    borderColor: "{colors.hairline}"
    backdropFilter: "blur(20px)"
    rounded: "{rounded.xl}"
    padding: 24px
  button-primary:
    backgroundColor: "{colors.primary-indigo}"
    textColor: "{colors.ink}"
    rounded: "{rounded.xl}"
    padding: 8px 16px
  button-cyan:
    backgroundColor: "{colors.primary-cyan}"
    textColor: "{colors.canvas}"
    rounded: "{rounded.xl}"
    padding: 8px 16px
  button-secondary:
    backgroundColor: "rgba(255, 255, 255, 0.05)"
    borderColor: "{colors.hairline}"
    textColor: "{colors.ink-muted}"
    rounded: "{rounded.xl}"
    padding: 8px 16px
  status-badge:
    rounded: "{rounded.pill}"
    padding: 2px 8px
    typography: "{typography.caption}"
---

## Overview

Antigravity AI employs a custom **Tactical Glassmorphism** design system. The user experience centers on dark-mode telemetry consoles, live agent streams, dynamic state-graphs, and data tables. Visual depth is established using semi-transparent overlays, hairline boundary rings, and blurred ambient light spots. Accent indicators (Cyan for network telemetry, Indigo for AI agents, Fuchsia for metrics, Emerald for conversions, and Orange for external CRM syncs) prevent information overload on data-dense views.

Key characteristics:
- **Void-Black Canvas**: The background is anchored at `#030712`, providing high-contrast readability for neon overlays.
- **Glass Card Architecture**: Every widget lives inside a `.glass-card` containing a light outline border (`rgba(255, 255, 255, 0.05)`) and `backdrop-filter: blur(12px)`.
- **Accent Lighting glows**: Active components incorporate a CSS drop-shadow/glow corresponding to their active channel state.
- **Typography Density**: High density fonts (`Space Grotesk` and `JetBrains Mono`) emphasize technical reliability.

---

## Colors

### Theme Accents
- **Neon Cyan** (`{colors.primary-cyan}`): Used for active system status, webhook updates, and real-time logs.
- **Indigo Blue** (`{colors.primary-indigo}`): Used for agent profiles, workflows, triggers, and primary interactive CTAs.
- **Fuchsia Pink** (`{colors.primary-fuchsia}`): Used for impressions, metrics graphs, and engagement status.
- **CRM Orange** (`{colors.crm-orange}`): Reserved exclusively for external CRM integration tokens, connection badges, and sync triggers (e.g., Twenty CRM, Google Sheets ledger).

### Surfaces
- **Canvas** (`{colors.canvas}`): The foundational background layer, `#030712`.
- **Surface Card** (`{colors.surface-card}`): Lightweight transparent card backing, `rgba(255, 255, 255, 0.03)`.
- **Surface Panel** (`{colors.surface-panel}`): Primary section backing, `rgba(0, 0, 0, 0.35)`.
- **Hairline** (`{colors.hairline}`): 1px borders separating layers, `rgba(255, 255, 255, 0.05)`.
- **Hairline Active** (`{colors.hairline-active}`): Highlighted border, `rgba(6, 182, 212, 0.2)`.

---

## Typography

The typography structure uses two main font stacks to contrast metadata and analytics:

| Token | Size | Weight | Line Height | Letter Spacing | Font Family | Use Cases |
|---|---|---|---|---|---|---|
| `{typography.display-xl}` | 56px | 700 | 1.10 | -1.5px | Space Grotesk | Main cinematic heroes, title statements |
| `{typography.display-lg}` | 40px | 700 | 1.15 | -1.0px | Space Grotesk | Section headers |
| `{typography.headline}` | 24px | 600 | 1.25 | -0.5px | Space Grotesk | Inner cards, table group labels |
| `{typography.card-title}` | 16px | 600 | 1.30 | -0.2px | Space Grotesk | Individual component headers |
| `{typography.body}` | 14px | 400 | 1.50 | 0px | Plus Jakarta Sans | Body text, explanation text blocks |
| `{typography.body-sm}` | 12px | 400 | 1.50 | 0px | Plus Jakarta Sans | Table values, labels |
| `{typography.caption}` | 10px | 400 | 1.40 | 0.2px | Plus Jakarta Sans | Subtitles, disabled indicators, badge texts |
| `{typography.eyebrow}` | 11px | 600 | 1.30 | 1.5px | JetBrains Mono | Micro headers, system metadata, subheadings |
| `{typography.mono}` | 12px | 400 | 1.50 | 0px | JetBrains Mono | Console logs, database rows, JSON parameters |

---

## Layout & Spacing

### Grid Structures
1. **Workspace Container**: The core layout spans 100% viewport width with a maximum boundary of `1600px` to map wide multi-column metrics correctly.
2. **Dashboard Grid**: The default telemetry dashboard uses a 4-column layout (`grid-cols-1 md:grid-cols-2 lg:grid-cols-4`) to position metrics cards side-by-side.
3. **Integrations Marketplace**: The integrations list is organized into a 5-column grid (`grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-5`) to host third-party endpoints.

### Spacing Principles
- Base padding uses the `8px` metric (xs).
- Inner card padding is locked to `16px` (md) or `24px` (lg).
- Main viewports separate using `16px` (md) gaps for maximum data density.

---

## Elevation & Depth

Antigravity AI does not use traditional shadows on dark canvasses. Depth is represented by borders and backdrop blurs:

1. **Flat (Canvas)**: Background surface of the app window.
2. **Level 1 (Card Lift)**: `.glass-card` backing (`rgba(255, 255, 255, 0.03)`) + 1px hairline border (`rgba(255, 255, 255, 0.05)`).
3. **Level 2 (Panel Lift)**: `.glass-panel` backing (`rgba(0, 0, 0, 0.35)`) + 1px hairline border + `backdrop-filter: blur(20px)`.
4. **Level 3 (Active Focus / Glow)**: Card border changes to `{colors.hairline-active}` + light shadow glow matching the component's accent color (e.g. `shadow-[0_0_12px_rgba(6,182,212,0.15)]`).

---

## Components

### Buttons
- **`button-primary`**: Used for primary user interactions. Features an indigo background with transition effects.
- **`button-cyan`**: Used for launching scripts or initializing node operations. High contrast black text on cyan background.
- **`button-secondary`**: Translucent background button with borders. Perfect for filters and secondary actions.

### Data Tables
- Header row uses `{typography.eyebrow}` in light grey text.
- Table body cells use `{typography.mono}` or `{typography.body-sm}`.
- Rows separate using `1px solid rgba(255, 255, 255, 0.05)`.
- Alternating rows remain un-shaded to preserve transparency.

### Status Badges
- **Active / Connected**: `{colors.semantic-success}` text with matching transparent green background + thin green border.
- **Simulated / Idle**: `{colors.semantic-warning}` text with matching transparent yellow background + thin yellow border.
- **Failed / Archived**: `{colors.semantic-danger}` text with transparent red background + thin red border.

---

## Do's and Don'ts

### Do
- Maintain a consistent dark aesthetic. Every panel must support the standard glass backdrop-blur.
- Use `CRM Orange` strictly for CRM/ledger connection and sync items.
- Ensure that data loading scripts have offline fallback simulators so the dashboard metrics remain visually populated.
- Keep table rows compact with minimal vertical padding to ensure visual telemetries fit within single-page folds.

### Don't
- Do not use true black `#000000` as the canvas. Always use the deep navy-gray `#030712`.
- Do not use solid card backgrounds. Cards must allow underlying canvas glow filters to pass through via transparency.
- Do not introduce unrelated third-party color gradients (e.g., bright green cards). Accents must match the specified color system.
- Do not make buttons with zero-radius corners. Use the standard `{rounded.xl}` (12px) curve.

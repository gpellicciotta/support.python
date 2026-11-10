---
skill:
  name: ui-guidelines
  description: >-
    Rules for visual design systems in projects with a user interface: design tokens, themes, components,
    patterns, and the style.css, visual-style-gallery.html, and visual-style-guide.md files.
    Use when designing, styling, theming, or documenting a web UI, or when adding or changing CSS.
---
# UI Guidelines
Rules for defining, implementing, and documenting the visual design of projects with a user interface.

## Scope
- Apply these guidelines to every project that exposes a human-facing web user interface.
- Read [visual-design-system-notes.md](../docs/notes/visual-design-system-notes.md) for background, terminology, and reference systems.

## Visual Design System
- Base every user interface on exactly one formal visual design system.
- Document at least its principles, design tokens, components, patterns, and usage rules.
- Prefer an existing shared design system of the same product family over creating a new one.
- Record the decision to create a new design system, with its reason, in the visual style guide.
- Design a system meant for sibling applications so they can consume it without copying files.

> Principles are a few adjectives and a mood that settle later debates about the look.
> Patterns are recurring combinations of components, such as a search toolbar or an empty state.

## Design Tokens
- Express colors, typography, spacing, radii, shadows, layers, and layout widths as CSS custom properties.
- Split tokens into a primitive tier holding raw values and a semantic tier naming roles.
- Reference only semantic tokens from component and page styles.
- Name semantic tokens after roles such as `--color-danger`, never after appearances such as `--red-text`.
- Never hard-code colors, font families, font sizes, spacing steps, radii, or shadows outside token definitions.
- Support light and dark themes by redefining semantic tokens only.
- Follow `prefers-color-scheme` by default and allow a `data-theme` attribute override on the root element.
- Meet WCAG 2.2 AA contrast for every semantic text and background pair in every theme.

> WCAG AA requires 4.5:1 for normal text, and 3:1 for large text and essential non-text elements.

## Components and Patterns
- Build components only from semantic tokens.
- Define every applicable state: default, hover, focus-visible, active, disabled, and error.
- Keep a visible focus indicator on every interactive element.
- Design mobile-first and support widths from 360 px phones to 1440 px desktops.
- Make touch targets at least 44 by 44 CSS pixels.
- Honor `prefers-reduced-motion` by disabling non-essential animations and transitions.

## Required Files for Project-Owned Systems
- Maintain three files for a design system the project creates itself:
  - `style.css`: the stylesheet entry point holding all tokens and component styles as usable code.
  - `visual-style-gallery.html`: a page rendering every token, component, state, and variation.
  - `visual-style-guide.md`: principles, choices, and usage rules, linking to the other two files.
- Place them at `{{web-root}}/css/style.css`, `{{web-root}}/demo/visual-style-gallery.html`, and `docs/specs/visual-style-guide.md`.
- Link the visual style guide from `docs/index.md`.

### Style Sheet
- Make `style.css` the single stylesheet entry point that every page links.
- Split large systems into partials imported by `style.css`, such as `tokens.css` and one file per component.
- Keep all token definitions together in one file, grouped by category with a short comment per group.
- Comment each component block with its purpose and its supported variants.

### Visual Style Gallery
- Load the real `style.css` plus at most one gallery-only stylesheet for specimen layout.
- Never use inline styles or hard-coded values on rendered specimens.
- Show every token group: named color swatches, type scale, spacing, radii, shadows, and layers.
- Show every component in every variant and state.
- Show every documented pattern composed from real components.
- Provide a light, dark, and system theme switch that sets the `data-theme` attribute.
- Render at phone and desktop widths without horizontal page scrolling.
- Use placeholder content only, never real user or family data.

> A gallery that adds its own styling shows things the real stylesheet does not produce.

### Visual Style Guide
- Summarize the principles and visual direction in a few sentences.
- Explain the intent and usage rules of each token group, linking to its definition instead of repeating values.
- Describe when to use and when not to use each component and pattern.
- Link each component and pattern to its gallery section.
- Record significant visual decisions with their rationale and rejected alternatives.

> Token values copied into Markdown tables drift as soon as the stylesheet changes.

## Projects Reusing a Shared System
- Consume a shared design system as a pinned, versioned dependency, never as hand-copied files.
- Add project-specific tokens and components in a project stylesheet loaded after the shared one.
- Override shared semantic tokens only for a deviation documented in the visual style guide.
- Keep a short `visual-style-guide.md` naming the shared system, its version, and every local addition.
- Show local components in a project gallery, or move them into the shared gallery once shared.

## Changing a Design System
- Change tokens and components in the stylesheets first, then update gallery and guide in the same commit.
- Treat renaming or removing a shared token or component class as a breaking change.
- Capture gallery screenshots before and after every visual change, following the Testing Guidelines.

## Verifying a Design System
- Serve the gallery locally and confirm it returns HTTP 200 with every stylesheet loaded.
- Screenshot the gallery in light and dark themes at 390 px and 1440 px widths.
- Fail verification on console errors, failed requests, horizontal page scrolling, or contrast below WCAG AA.
- Search stylesheets outside token definitions for raw color literals and fail on any match.

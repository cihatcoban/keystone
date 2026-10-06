# Accessibility Checklist (WCAG 2.2 AA, practical subset)

Automated tooling catches roughly a third of real issues. The keyboard pass
catches most of the rest, and takes two minutes.

## Structure

- [ ] Semantic elements: `button`, `a`, `nav`, `main`, `h1`–`h6` in order
- [ ] One `h1` per page; headings describe structure, not styling
- [ ] Landmarks present; a skip link to main content
- [ ] Page has a descriptive, unique `title`
- [ ] `lang` attribute set correctly

## Keyboard

- [ ] Every interactive element reachable by Tab, in a logical order
- [ ] Visible focus indicator everywhere (never `outline: none` without a
      replacement)
- [ ] No keyboard trap; Escape closes dialogs and menus
- [ ] Focus moves into a dialog on open and returns to the trigger on close
- [ ] Focus managed on route change (to the heading or main region)
- [ ] Custom widgets implement the expected key patterns (arrows in menus,
      Home/End in lists)

## Forms

- [ ] Every input has a programmatically associated label (not placeholder-only)
- [ ] Errors identified in text, linked to the field, announced on change
- [ ] Required fields indicated in text, not by color alone
- [ ] Inputs have appropriate `type` and `autocomplete`
- [ ] Grouped controls use `fieldset`/`legend`

## Content

- [ ] Images: meaningful `alt`, or `alt=""` when decorative
- [ ] Contrast ≥ 4.5:1 body text, ≥ 3:1 large text and UI boundaries
- [ ] Meaning never carried by color alone
- [ ] Text resizes to 200% without loss of content or function
- [ ] Usable at 320 px width without horizontal scrolling
- [ ] Touch targets ≥ 24×24 px with spacing

## Dynamic

- [ ] Live regions announce async updates (with the right politeness)
- [ ] Loading, empty and error states are perceivable, not visual-only
- [ ] `prefers-reduced-motion` respected; nothing flashes more than 3×/second
- [ ] Time limits adjustable or absent

## Verify

1. Unplug the mouse and complete the primary task
2. Run an automated checker (axe) — zero violations
3. Zoom to 200% and to 320 px width
4. One pass with a screen reader on the critical flow

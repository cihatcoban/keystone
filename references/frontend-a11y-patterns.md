# Frontend Accessibility Patterns

Detail for `frontend-architecture`. `references/accessibility-checklist.md` says
*what* must hold; this file says *how* the common widgets meet it. Patterns
follow the WAI-ARIA Authoring Practices and WCAG 2.2 AA. Checked against those
specifications on 2026-10-22.

Two rules first:

1. **Native element before ARIA.** `button`, `a`, `dialog`, `details`,
   `select`, `input type=…` bring keyboard, focus and semantics for free. ARIA
   only changes what assistive technology is *told*; it adds no behavior.
   Wrong ARIA is worse than none.
2. **Every pattern has a keyboard script.** Run it with the mouse unplugged
   before calling the widget done.

## Action or navigation

| Does it… | Element | Never |
|---|---|---|
| Go somewhere (URL changes) | `a href` | `button` with a click handler that navigates |
| Do something (submit, open, toggle) | `button type="button"` | `div`/`span` with a click handler |

Icon-only buttons need an accessible name: visually hidden text, or
`aria-label`. Decorative icons inside a labelled button get `aria-hidden="true"`.

## Modal dialog

- Use the native `dialog` element opened with its modal method (`showModal()`):
  the rest of the page becomes inert, Escape closes it, and it renders above
  everything without z-index fights.
- Name it: `aria-labelledby` pointing to the dialog's heading.
- On open, focus the first meaningful control — or the heading (with
  `tabindex="-1"`) when the dialog starts with content to read.
- On close, return focus to the element that opened it. If that element is
  gone, focus its nearest logical successor, never `body`.
- Do not hand-roll a focus trap when the native modal is available.

Keyboard script: open with Enter → Tab cycles inside only → Escape closes →
focus is back on the trigger.

## Disclosure (show more, accordion section)

- `details`/`summary` when the styling allows; otherwise a `button` with
  `aria-expanded="true|false"` and `aria-controls` naming the panel.
- Accordion headers are buttons inside headings, so heading navigation still
  works.

## Menu button

For application-style command menus only. Site navigation is a list of links
in a `nav`, optionally behind a disclosure button — not `role="menu"`.

- Button: `aria-haspopup="menu"`, `aria-expanded`.
- List: `role="menu"`, items `role="menuitem"`; only one item is in the tab
  order at a time (roving `tabindex`).
- Keys: Enter/Space/Down opens and focuses the first item; Up/Down move;
  Home/End jump; Escape closes and returns focus to the button; Tab closes and
  moves on.

## Tabs

- `role="tablist"` containing `role="tab"` elements; each tab has
  `aria-selected` and `aria-controls`; each panel has `role="tabpanel"` and
  `aria-labelledby` pointing back to its tab.
- Only the selected tab is in the tab order. Left/Right move between tabs,
  Home/End jump; Tab moves into the panel.
- Activate on arrow (automatic) when panels render instantly; require
  Enter/Space (manual) when switching is expensive.

## Combobox / autocomplete

- Prefer a native `select` or `input` + `datalist` when they meet the need.
- Custom: the input has `role="combobox"`, `aria-expanded`, `aria-controls`
  pointing to a `role="listbox"`; the highlighted option is referenced by
  `aria-activedescendant` while focus **stays in the input**.
- Announce the result count through a polite live region ("5 results").
- Escape closes the list; a second Escape may clear the input.

## Forms and errors

- Every control has a programmatic label; hints and errors are linked with
  `aria-describedby`; an invalid field gets `aria-invalid="true"`.
- On a failed submit: render an error summary at the top with links to each
  field, move focus to it, and keep every message next to its field too.
- Validate on blur or submit, not on every keystroke; never clear what the
  user typed because it was invalid.
- Required, invalid and success states are stated in text, not only by color.

## Status messages and toasts

- Polite updates ("Saved", "3 results"): `role="status"`. Urgent, blocking
  problems: `role="alert"` — sparingly; it interrupts.
- The live region must already be in the page **before** its text changes;
  inserting a region together with its message is often not announced.
- A toast that disappears on its own must not contain the only way to act
  (an Undo); put the action somewhere persistent or keep the toast until
  dismissed.

## Route change in a single-page app

After client-side navigation:

1. Update the document title to the new page's unique title.
2. Move focus to the new page's main heading (`tabindex="-1"`) or main region,
   unless the framework already does a deliberate equivalent
   (`references/frontend-framework-map.md`).
3. Do not move focus for in-page updates such as filtering — announce them.

A skip link to the main region is the first focusable element and becomes
visible on focus.

## Loading and async regions

- Mark the updating region `aria-busy="true"` while it loads; give a spinner an
  accessible name.
- Never move focus to a spinner, and never move focus when content arrives
  unless the user asked for it.
- Reserve the space content will occupy (layout shift is an accessibility
  problem for magnifier users as well as a CLS problem).

## Pointer, motion and focus visibility

- Dragging (reorder, slider, map pan) has a single-pointer or keyboard
  alternative (WCAG 2.5.7).
- Animation and parallax respect the reduced-motion preference in both styles
  and script.
- The focus indicator is visible, not hidden under sticky headers or footers
  (WCAG 2.4.11); use `:focus-visible` rather than removing outlines.

## Data tables

Use real `table` markup with a `caption`, header cells with `scope`, and
sortable headers as buttons that expose `aria-sort` on the header cell.

## Native mobile

The same rules apply through the platform accessibility API: every control has
a label and a role (trait), focus order follows reading order, announcements go
through the platform's announcement call, and dynamic type and reduced motion
are respected. Verify with VoiceOver and TalkBack on a device.

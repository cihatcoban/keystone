# Frontend Framework Map

Lookup for `frontend-architecture` (see
[ADR-002](../docs/adr/ADR-002-stack-specific-references.md)): where each rule
of the skill lives in a given framework, and the trap that breaks it there.
It adds no rules — when this file and the skill disagree, the skill wins.

**Checked against:** React 19.2, Vue 3.5, Angular 22, Svelte 5 with
SvelteKit 2 — on 2026-10-22. Confirm the project's versions during stack
discovery; an API named here may not exist in an older version. For a
framework not listed, apply the skill directly and say this lookup was missing.

Read only the section for the project's framework.

## React 19

| Skill rule | Where it lives | Trap |
|---|---|---|
| Local UI state | `useState` / `useReducer` in the owning component | Lifting state "just in case" until every keystroke re-renders the page |
| Derived state is computed | Compute during render; `useMemo` only after profiling shows cost | An effect that copies props or state into other state — one stale frame per change, and loops |
| Server state is a cache | A query-cache library or the router/meta-framework's data loading | `fetch` in an effect plus `useState` — no caching, no dedupe, races |
| URL state | The router's search-params API | Filters held in component state, lost on reload and back |
| Small global state | Context for rarely changing values (theme, session); an external store via `useSyncExternalStore` for frequent updates | One context holding everything — every consumer re-renders on every change |
| Out-of-order responses | Abort in the effect's cleanup (`AbortController`); query libraries pass a signal | Development mode runs effects twice; a cleanup that does not abort shows the race immediately — fix it, do not disable the mode |
| Error state | Error boundaries catch **render** errors only | Assuming a boundary catches event-handler or async errors — those need the query's error state |
| Route code splitting | `lazy` + `Suspense`, or the router's lazy routes | One bundle for all routes |
| Focus management | A ref, focused after mount; native `dialog` via the ref's `showModal()` | Calling `focus()` during render |
| Forms | Native `form` with actions / `useActionState`, or a form library | Server errors shown as a toast instead of mapped to fields |
| Long lists | A windowing library | Index as `key` in a list that reorders — state attaches to the wrong row |
| Rendering cost | Profile with the React DevTools Profiler first. React Compiler memoizes automatically where the project enables it; otherwise `memo` / `useMemo` / `useCallback` only where the profile shows wasted renders | Hand-memoizing everything: cost without a measured gain, and stale closures |
| Component tests | React Testing Library: query by role, label and text; `user-event` for interaction | Asserting on state, hooks or class names — breaks on refactor, misses accessibility regressions |

## Vue 3.5

| Skill rule | Where it lives | Trap |
|---|---|---|
| Local UI state | `ref` / `reactive` in the component | Destructuring a `reactive` object — the copies stop updating (`toRefs`) |
| Derived state is computed | `computed()` | A `watch` that assigns a derived value to another ref |
| Server state is a cache | A query-cache library, or the meta-framework's data loading (`useFetch` / `useAsyncData` in Nuxt) | Server data copied into a Pinia store and edited there |
| URL state | `useRoute().query` and `router.replace({ query })` | Query read once in setup and never watched |
| Small global state | A Pinia store | A store per component, or server data in it |
| Out-of-order responses | Abort in `onWatcherCleanup()` or the watcher's `onCleanup` argument | A watcher that fires a request per change without cancelling the previous one |
| Error state | `onErrorCaptured` in an ancestor; `app.config.errorHandler` for reporting; render each async branch explicitly | Relying on `Suspense`, which is still experimental, as the only loading and error UI |
| Route code splitting | Route `component: () => import(...)`; `defineAsyncComponent` | Static imports of every page in the router file |
| Focus management | Template ref; `await nextTick()` then `focus()` | Focusing before the element is rendered |
| Forms | `v-model` with explicit validation timing | Validating on every input event, errors flashing while typing |
| Long lists | A virtual-scroller library | `v-if` and `v-for` on the same element |
| Rendering cost | Keep child props stable; `v-once` / `v-memo` for large subtrees that rarely change; `shallowRef` for large data replaced rather than mutated | Deep reactivity over very large structures; a computed that returns a new object every run |
| Component tests | Vue Test Utils or Vue Testing Library: mount, interact, assert rendered output | Reaching into `wrapper.vm` internals |

## Angular 22

| Skill rule | Where it lives | Trap |
|---|---|---|
| Local UI state | `signal()` in the component | Plain fields changed from timers or subscriptions in a zoneless app — the view does not update |
| Derived state is computed | `computed()`; `linkedSignal()` when a derived value may be overridden locally | An `effect()` that writes signals to keep values in sync |
| Server state is a cache | `httpResource()` / `resource()` (stable since v22), exposing value, loading and error signals; or `HttpClient` observables with an explicit state model | Subscribing in the component and copying results into fields |
| URL state | `ActivatedRoute` query params, or route params bound to inputs (`withComponentInputBinding`) | Mirroring the query string into a service by hand |
| Small global state | A root-provided service holding signals, or a signal store library | A global store holding server data |
| Out-of-order responses | A resource aborts the superseded request when its params change; with RxJS, `switchMap` | `mergeMap` for search-as-you-type; subscriptions without `takeUntilDestroyed` |
| Error state | The resource's `error()` rendered in the template; a global `ErrorHandler` for reporting only | Expecting a component-level error boundary — there is none; every async view needs its error branch |
| Route code splitting | `loadComponent` / `loadChildren`; `@defer` for below-the-fold content | Eagerly imported feature routes |
| Focus and announcements | CDK a11y: `cdkTrapFocus`, `FocusMonitor`, `LiveAnnouncer`; focus after render with `afterNextRender` | Focusing in the constructor |
| Forms | Typed reactive forms; `updateOn: 'blur'` to control validation timing | Untyped form groups — field renames fail silently |
| Long lists | CDK virtual scroll viewport | Rendering thousands of rows in one `@for` |
| Rendering cost | `OnPush` components with signals; `@for` tracking a stable id; `@defer` for heavy content below the fold | Tracking by the item object, or by `$index` in a list that reorders — rows are re-created |
| Component tests | `TestBed` with CDK component harnesses, or Angular Testing Library | Calling private methods or reading private fields from the test |

## Svelte 5 and SvelteKit 2

| Skill rule | Where it lives | Trap |
|---|---|---|
| Local UI state | `$state` | Destructuring a `$state` object — the parts are snapshots |
| Derived state is computed | `$derived` | An `$effect` that assigns to state to mirror another value |
| Server state is a cache | SvelteKit `load` functions, revalidated with `invalidate()` | Fetching in `onMount` and storing in component state |
| URL state | `page.url.searchParams` from `$app/state` (`$app/stores` is the legacy module); `goto(url, { replaceState: true, keepFocus: true })` | Filters in component state that the URL never sees |
| Small global state | Shared `$state` in a `.svelte.js` / `.svelte.ts` module on the client; context (`setContext`) for per-request data | Module-level state during server rendering — it is shared across every request and user |
| Out-of-order responses | Return a cleanup function from `$effect` and abort there | An effect that starts a request on every change and never cancels |
| Error state | `<svelte:boundary>` with a `failed` snippet (render and effect errors only); `+error.svelte` per route | Assuming the boundary catches event-handler or `setTimeout` errors |
| Route code splitting | Automatic per route; dynamic `import()` for heavy components | Importing a heavy library in the root layout |
| Focus management | SvelteKit focuses `body` after navigation and announces the page `<title>`; move focus to the heading in `afterNavigate` if the design needs it | Pages sharing one `<title>` — every navigation is announced identically |
| Forms | Form actions with `use:enhance`; return `fail(400, { … })` to map field errors | Client-only submit handlers that break without JavaScript |
| Long lists | A virtual-list component | Rendering an unbounded `{#each}` |
| Rendering cost | Updates are fine-grained by default; `$state.raw` for large arrays and objects replaced rather than mutated | Deep `$state` proxies over large data that is never mutated in place |
| Component tests | Svelte Testing Library with the project's test runner; `flushSync()` or `await tick()` before asserting after a state change | Asserting before the DOM has updated |

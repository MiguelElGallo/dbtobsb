# Pass 5: Rendered usability and accessibility

- Scope: Zensical desktop and 375-pixel rendering, navigation, diagrams, tables,
  code, and accessibility tree
- Verdict: `CHANGES_REQUIRED`, then resolved
- Review date: 2026-07-18

## Findings

1. The Mermaid diagram depended on an external runtime script and could remain raw
   source in a restricted network.
2. The rendered Mermaid shadow tree had no usable text equivalent.
3. The floating back-to-top control covered prose at narrow width.
4. Removing SuperFences while replacing Mermaid collapsed the text flow into inline
   code.
5. The upstream theme marks the active page visually but does not emit
   `aria-current="page"`.

## Resolution

- Replaced Mermaid with a complete text flow available in the accessibility tree.
- Kept an empty local SuperFences extension so the flow renders as an 11-line
  preformatted block without external scripts.
- Disabled the floating back-to-top control.
- Accepted the missing `aria-current` as a nonblocking upstream-theme limitation
  for this private local release. Breadcrumbs, unique page headings, descriptive
  navigation labels, and visual active state remain available.

## Re-review result

`PASS`: fresh strict builds at desktop and 375 pixels had no page overflow, content
overlap, Mermaid dependency, external script, browser warning, or browser error.
Wide tables and code remain contained with horizontal scrolling.

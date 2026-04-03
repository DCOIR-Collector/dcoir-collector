# Attention Modes

## Placement modes
- `header`: place the banner before the response body
- `footer`: place the banner after the response body
- `dual`: place matching banners at both top and bottom

## Selection defaults
- `session-start` -> header
- `milestone` -> dual
- `review` -> footer or dual depending on importance
- `complete` -> footer
- `action-required` -> dual
- `blocked` -> dual

## Formatting principle
Use a wide border line, uppercase class label, and one short message line.

## Reliability note
Treat color as unreliable. Prefer border strength, uppercase labels, dual placement, and direct wording over client-dependent styling.

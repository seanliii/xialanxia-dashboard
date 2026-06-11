# project-xialanxia-dashboard

**Type:** project
**Updated:** 2026-03-20T11:17:04.348Z

## Facts

- Requires the JS tab controller to initialize after DOMContentLoaded to avoid element-not-found errors.
- The original tab control used pure CSS radio inputs before switching to JavaScript tab control introduced timing issues.
- Uses a tab switching UI controlled by pure CSS radios in its stable version
- Attempted JavaScript tab switching caused layered UI issues related to timing of the JS execution relative to DOM readiness
- Receives dynamic portfolio data loads from project-portfolio-scanner without affecting core HTML structure
- Uses pure CSS radio buttons for tab switching to ensure stability
- Portfolio scanner data updated dynamically via JavaScript
- Experienced a layering bug caused by premature JavaScript tab initialization
- User maintains an automated dashboard at https://seanliii.github.io/xialanxia-dashboard/ showing memory summarizations, push history, portfolio data, and frontend fixes.
- Dashboard displays portfolio data such as total assets and profit/loss.
- User fixed bugs with incorrect total assets and duplicate HTML elements in the dashboard.

## Connected to

- [[project-portfolio-scanner]] — loads dynamic portfolio data from
- [[project-portfolio-scanner]] — uses dynamic data updates from
- [[project-portfolio-scanner]] — visualizes data refreshed by
- [[user]] — maintains and fixes bugs in (reverse)

## Activity

- 2026-03-20: Mentioned in conversation
- 2026-03-20: Mentioned in conversation
- 2026-03-20: Mentioned in conversation
- 2026-03-20: Mentioned in conversation
- 2026-03-20: Mentioned in conversation
- 2026-03-20: Mentioned in conversation

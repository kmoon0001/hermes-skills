## Graph Explorer Access Token Extraction Reference

- **Tab selector**: `text=Access token` (use `.first()` if duplicates).
- **Copy button selector**: `button:has-text("Copy")` (ensure `[visible=true]`).
- **Token element selector**: `div:has-text("eyJ")` captures JWT prefix.
- **Typical snippet**:
  ```js
  await page.locator('text=Access token').first().click();
  await page.locator('button:has-text("Copy")[visible=true]').click();
  const token = await page.locator('div:has-text("eyJ")').innerText();
  console.log('Token:', token);
  ```
- **Pitfalls**: duplicated tab elements, truncated snapshot view, hidden copy button.
- **Use case**: automating Graph Explorer queries where a bearer token is needed for downstream API calls.
